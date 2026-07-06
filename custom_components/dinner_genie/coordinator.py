from __future__ import annotations

import logging
import random
from datetime import timedelta
from typing import Any
from uuid import uuid4

from homeassistant.components.todo import TodoItemStatus
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DinnerGenieApiError, DinnerGenieClient
from .const import DOMAIN, OPT_DAYS, OPT_DIET_TYPE, OPT_RECIPE_TYPE, OPT_SERVINGS

_LOGGER = logging.getLogger(__name__)


class DinnerGenieCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: DinnerGenieClient) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(hours=6))
        self.entry = entry
        self.client = client

    @property
    def days(self) -> int:
        return int(self.entry.options.get(OPT_DAYS, 5))

    @property
    def servings(self) -> int:
        return int(self.entry.options.get(OPT_SERVINGS, 4))

    @property
    def filters(self) -> dict[str, Any]:
        return {
            "dietType": self.entry.options.get(OPT_DIET_TYPE, "all"),
            "recipeType": self.entry.options.get(OPT_RECIPE_TYPE, "dinner"),
        }

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            recipes = await self.client.recipes(limit=500)
        except DinnerGenieApiError as err:
            raise UpdateFailed(str(err)) from err

        old = self.data or {}
        return {
            "recipes": recipes,
            "random": old.get("random"),
            "week_plan": old.get("week_plan"),
            "meals": old.get("meals", []),
            "shopping_lines": old.get("shopping_lines", []),
            "shopping_items": old.get("shopping_items", []),
        }

    async def async_generate_week_plan(self) -> None:
        try:
            week_plan = await self.client.week_plan(self.days, self.servings, **self.filters)
        except DinnerGenieApiError as err:
            raise UpdateFailed(str(err)) from err

        data = dict(self.data or {})
        data["week_plan"] = week_plan
        shopping_lines = week_plan.get("shoppingLines", []) or []

        data["meals"] = week_plan.get("meals", []) or []
        data["shopping_lines"] = shopping_lines
        data["shopping_items"] = self._todo_items_from_lines(shopping_lines)
        self.async_set_updated_data(data)

    async def async_choose_random_recipe(self) -> None:
        try:
            random_recipe = await self.client.random(**self.filters)
        except DinnerGenieApiError as err:
            raise UpdateFailed(str(err)) from err

        data = dict(self.data or {})
        data["random"] = random_recipe
        self.async_set_updated_data(data)

    async def async_replace_day(self, day_number: int) -> None:
        """Replace one meal in the current week menu and rebuild the shopping list."""
        data = dict(self.data or {})
        meals = list(data.get("meals") or [])
        index = day_number - 1

        if index < 0 or index >= len(meals):
            raise UpdateFailed(f"Dag {day_number} heeft nog geen gerecht om te vervangen")

        try:
            response = await self.client.recipes(limit=500, **self.filters)
        except DinnerGenieApiError as err:
            raise UpdateFailed(str(err)) from err

        recipes = [recipe for recipe in response.get("recipes", []) if isinstance(recipe, dict)]
        if not recipes:
            raise UpdateFailed("Geen recepten gevonden om mee te vervangen")

        current_ids = {str(meal.get("id")) for meal in meals if isinstance(meal, dict) and meal.get("id")}
        other_ids = {
            str(meal.get("id"))
            for pos, meal in enumerate(meals)
            if pos != index and isinstance(meal, dict) and meal.get("id")
        }

        candidates = [
            recipe
            for recipe in recipes
            if recipe.get("id") and str(recipe.get("id")) not in current_ids
        ]

        # If the recipe pool is too small, at least prevent duplicates with the other days.
        if not candidates:
            candidates = [
                recipe
                for recipe in recipes
                if recipe.get("id") and str(recipe.get("id")) not in other_ids
            ]

        if not candidates:
            raise UpdateFailed("Geen alternatief gerecht gevonden dat niet al in het weekmenu staat")

        new_recipe = random.choice(candidates)
        meals[index] = new_recipe

        shopping_lines = self._build_shopping_lines(meals)
        data["meals"] = meals
        data["shopping_lines"] = shopping_lines
        data["shopping_items"] = self._todo_items_from_lines(
            shopping_lines,
            previous_items=data.get("shopping_items") or [],
        )

        week_plan = dict(data.get("week_plan") or {})
        week_plan["meals"] = meals
        week_plan["shoppingLines"] = shopping_lines
        week_plan["days"] = len(meals)
        week_plan["servings"] = self.servings
        data["week_plan"] = week_plan

        self.async_set_updated_data(data)

    async def async_update_option(self, key: str, value: Any) -> None:
        options = dict(self.entry.options)
        options[key] = value
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        self.async_update_listeners()

    def _todo_items_from_lines(
        self,
        shopping_lines: list[str],
        previous_items: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        previous_by_summary = {
            str(item.get("summary")): item
            for item in (previous_items or [])
            if item.get("summary")
        }

        items: list[dict[str, Any]] = []
        for line in shopping_lines:
            summary = str(line)
            previous = previous_by_summary.get(summary)
            items.append(
                {
                    "uid": str(previous.get("uid")) if previous else str(uuid4()),
                    "summary": summary,
                    "status": previous.get("status", TodoItemStatus.NEEDS_ACTION) if previous else TodoItemStatus.NEEDS_ACTION,
                }
            )
        return items

    def _build_shopping_lines(self, meals: list[dict[str, Any]]) -> list[str]:
        """Build a shopping list from the current meals.

        Dinner Genie returns a scaled shopping list for generated week plans. When one
        day is replaced locally, we rebuild the list from ingredientsV2 and scale each
        recipe to the configured number of servings.
        """
        aggregated: dict[tuple[str, str], float] = {}
        display_names: dict[tuple[str, str], str] = {}
        loose_lines: list[str] = []

        for meal in meals:
            if not isinstance(meal, dict):
                continue

            recipe_servings = self._safe_float(meal.get("servings")) or float(self.servings or 1)
            scale = float(self.servings or 1) / recipe_servings if recipe_servings else 1.0
            ingredients_v2 = meal.get("ingredientsV2") or []

            if isinstance(ingredients_v2, list) and ingredients_v2:
                for ingredient in ingredients_v2:
                    if not isinstance(ingredient, dict):
                        continue

                    name = str(ingredient.get("name") or "").strip()
                    unit = str(ingredient.get("unit") or "").strip()
                    amount = self._safe_float(ingredient.get("amount"))

                    if not name:
                        continue

                    if amount is None:
                        loose_lines.append(name)
                        continue

                    key = (name.casefold(), unit.casefold())
                    aggregated[key] = aggregated.get(key, 0.0) + amount * scale
                    display_names[key] = name
                continue

            fallback = meal.get("ingredients") or []
            if isinstance(fallback, list):
                loose_lines.extend(str(item) for item in fallback if item)

        lines: list[str] = []
        for key in sorted(aggregated, key=lambda item: display_names[item].casefold()):
            amount = self._format_amount(aggregated[key])
            unit = key[1]
            name = display_names[key]
            parts = [amount]
            if unit:
                parts.append(unit)
            parts.append(name)
            lines.append(" ".join(parts))

        lines.extend(loose_lines)
        return lines

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _format_amount(value: float) -> str:
        rounded = round(value, 2)
        if rounded.is_integer():
            return str(int(rounded))
        return str(rounded).rstrip("0").rstrip(".")
