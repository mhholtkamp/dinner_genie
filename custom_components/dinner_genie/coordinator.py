from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DinnerGenieApiError, DinnerGenieClient
from .const import DEFAULT_SCAN_INTERVAL_HOURS, DOMAIN, STORAGE_KEY_PREFIX, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)


class DinnerGenieCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, client: DinnerGenieClient, entry_id: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=DEFAULT_SCAN_INTERVAL_HOURS),
        )
        self.client = client
        self.store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}_{entry_id}",
        )
        self._stored_week_plan: dict[str, Any] = {}

    async def async_load_stored_data(self) -> None:
        self._stored_week_plan = await self.store.async_load() or {}

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            recipes = await self.client.recipes()
            random_recipe = await self.client.random()
        except DinnerGenieApiError as err:
            raise UpdateFailed(str(err)) from err

        stored = self._stored_week_plan or {}
        return {
            "recipes": recipes,
            "random": random_recipe,
            "week_plan": stored,
            "meals": stored.get("meals", []),
            "shopping_lines": stored.get("shoppingLines", []),
        }

    async def async_generate_week_plan(self, days: int, servings: int) -> None:
        try:
            week_plan = await self.client.week_plan(days, servings)
        except DinnerGenieApiError as err:
            raise UpdateFailed(str(err)) from err

        self._stored_week_plan = week_plan
        await self.store.async_save(week_plan)

        data = dict(self.data or {})
        data["week_plan"] = week_plan
        data["meals"] = week_plan.get("meals", [])
        data["shopping_lines"] = week_plan.get("shoppingLines", [])
        self.async_set_updated_data(data)
