from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, HELPER_DAYS, HELPER_SERVINGS

_LOGGER = logging.getLogger(__name__)


def _read_int_helper(hass: HomeAssistant, entity_id: str, default: int) -> int:
    state = hass.states.get(entity_id)
    if state is None or state.state in {"unknown", "unavailable", "none", "None"}:
        _LOGGER.warning("Helper %s niet gevonden of ongeldig. Default %s wordt gebruikt", entity_id, default)
        return default
    try:
        return int(float(state.state))
    except (TypeError, ValueError):
        _LOGGER.warning("Helper %s heeft geen getalwaarde: %s. Default %s wordt gebruikt", entity_id, state.state, default)
        return default


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DinnerGenieGenerateWeekMenuButton(coordinator, entry.entry_id)])


class DinnerGenieGenerateWeekMenuButton(CoordinatorEntity, ButtonEntity):
    _attr_name = "Dinner Genie genereer weekmenu"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_generate_week_menu"

    async def async_press(self) -> None:
        days = _read_int_helper(self.coordinator.hass, HELPER_DAYS, 5)
        servings = _read_int_helper(self.coordinator.hass, HELPER_SERVINGS, 4)

        days = max(1, min(days, 14))
        servings = max(1, min(servings, 50))

        await self.coordinator.async_generate_week_plan(days, servings)
