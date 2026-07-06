from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MAX_DAYS, MAX_SERVINGS, MIN_DAYS, MIN_SERVINGS, OPT_DAYS, OPT_SERVINGS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        DinnerGenieNumber(coordinator, OPT_DAYS, "Aantal dagen", MIN_DAYS, MAX_DAYS, 1),
        DinnerGenieNumber(coordinator, OPT_SERVINGS, "Aantal personen", MIN_SERVINGS, MAX_SERVINGS, 1),
    ])


class DinnerGenieNumber(NumberEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, option_key: str, name: str, min_value: int, max_value: int, step: int) -> None:
        self.coordinator = coordinator
        self.option_key = option_key
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{option_key}"
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_mode = "box"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.coordinator.entry.entry_id)}, "name": "Dinner Genie"}

    @property
    def native_value(self) -> int:
        return int(self.coordinator.entry.options.get(self.option_key, 5 if self.option_key == OPT_DAYS else 4))

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_update_option(self.option_key, int(value))
