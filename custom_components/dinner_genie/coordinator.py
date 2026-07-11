from __future__ import annotations

import logging
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
        day_entries = (self.data or {}).get("day_entries") or []
        if day_entries:
            return len(day_entries)
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
            week_planning_response = await self.client.week_planning()
        except DinnerGenieApiError as err:
            raise UpdateFailed(str(err)) from err

        old = self.data or {}
        week_planning = self._week_planning_payload(week_planning_response)
        day_entries = self._day_entries_from_week_planning(week_planning)
        meals = [entry["recipe"] for entry in day_entries if isinstance(entry.get("recipe"), dict)]
        shopping_lines = self._shopping_lines_from_week_planning(week_planning)
        return {
            "recipes": recipes,
            "random": old.get("random"),
            "week_plan": week_planning,
            "day_entries": day_entries,
            "meals": meals,
            "shopping_lines": shopping_lines,
            "shopping_items": self._todo_items_from_lines(
                shopping_lines,
                previous_items=old.get("shopping_items") or [],
            ),
        }

    async def async_generate_week_plan(self) -> None:
        await self.async_request_refresh()

    async def async_choose_random_recipe(self) -> None:
        try:
            random_recipe = await self.client.random(**self.filters)
        except DinnerGenieApiError as err:
            raise UpdateFailed(str(err)) from err

        data = dict(self.data or {})
        data["random"] = random_recipe
        self.async_set_updated_data(data)

    async def async_replace_day(self, day_number: int) -> None:
        raise UpdateFailed("Weekplanning wordt nu beheerd in Savelio. Vernieuw de integratie om wijzigingen op te halen.")

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

    @staticmethod
    def _week_planning_payload(response: dict[str, Any]) -> dict[str, Any]:
        for key in ("weekPlanning", "week_planning", "planning", "weekPlan", "week_plan"):
            value = response.get(key)
            if isinstance(value, dict):
                return value
        return response

    def _day_entries_from_week_planning(self, week_planning: dict[str, Any]) -> list[dict[str, Any]]:
        raw_days = self._first_list(
            week_planning,
            "days",
            "dayPlans",
            "day_plans",
            "planning",
            "items",
            "meals",
        )
        entries: list[dict[str, Any]] = []

        for index, item in enumerate(raw_days, start=1):
            if not isinstance(item, dict):
                if isinstance(item, str):
                    continue
                recipe = item if isinstance(item, dict) else {}
                entry = {"day": index, "recipe": recipe}
                entries.append(entry)
                continue

            recipe = self._recipe_from_day_item(item)
            if not isinstance(recipe, dict) or not recipe:
                continue

            entry = {
                "day": item.get("day") or item.get("dayNumber") or item.get("day_number") or index,
                "date": item.get("date") or item.get("plannedDate") or item.get("planned_date"),
                "weekday": item.get("weekday") or item.get("dayName") or item.get("day_name"),
                "label": item.get("label") or item.get("title"),
                "recipe": recipe,
            }
            self._copy_day_metadata_to_recipe(entry, recipe)
            entries.append(entry)

        return entries

    def _recipe_from_day_item(self, item: dict[str, Any]) -> dict[str, Any]:
        for key in ("recipe", "meal", "dinner", "dish"):
            value = item.get(key)
            if isinstance(value, dict):
                return dict(value)
        return dict(item)

    @staticmethod
    def _copy_day_metadata_to_recipe(entry: dict[str, Any], recipe: dict[str, Any]) -> None:
        for source, target in (
            ("day", "planning_day"),
            ("date", "planning_date"),
            ("weekday", "planning_weekday"),
            ("label", "planning_label"),
        ):
            if entry.get(source) not in (None, ""):
                recipe[target] = entry[source]

    def _shopping_lines_from_week_planning(self, week_planning: dict[str, Any]) -> list[str]:
        raw_lines = self._first_list(
            week_planning,
            "shoppingLines",
            "shopping_lines",
            "shoppingList",
            "shopping_list",
            "groceryLines",
            "grocery_lines",
            "groceries",
        )

        lines: list[str] = []
        for item in raw_lines:
            if isinstance(item, str) and item.strip():
                lines.append(item.strip())
            elif isinstance(item, dict):
                summary = item.get("summary") or item.get("name") or item.get("label") or item.get("title")
                if summary:
                    lines.append(str(summary))
        return lines

    @staticmethod
    def _first_list(data: dict[str, Any], *keys: str) -> list[Any]:
        for key in keys:
            value = data.get(key)
            if isinstance(value, list):
                return value
        return []

    def _build_shopping_lines(self, meals: list[dict[str, Any]]) -> list[str]:
        """Build a shopping list from the current meals.

        Legacy helper kept for compatibility with older data. Savelio now returns the
        current shopping list with the weekplanning, so normal refreshes no longer
        rebuild this locally.
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
