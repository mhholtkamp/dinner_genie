from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any
from uuid import uuid4

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
        data["shopping_items"] = [
            {
                "uid": str(uuid4()),
                "summary": str(line),
                "status": "needs_action",
            }
            for line in shopping_lines
        ]
        self.async_set_updated_data(data)

    async def async_choose_random_recipe(self) -> None:
        try:
            random_recipe = await self.client.random(**self.filters)
        except DinnerGenieApiError as err:
            raise UpdateFailed(str(err)) from err

        data = dict(self.data or {})
        data["random"] = random_recipe
        self.async_set_updated_data(data)

    async def async_update_option(self, key: str, value: Any) -> None:
        options = dict(self.entry.options)
        options[key] = value
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        self.async_update_listeners()
