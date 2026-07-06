from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DIET_OPTIONS, DOMAIN, OPT_DIET_TYPE, OPT_RECIPE_TYPE, RECIPE_TYPE_OPTIONS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        DinnerGenieSelect(coordinator, OPT_DIET_TYPE, "Dieet", DIET_OPTIONS, "all"),
        DinnerGenieSelect(coordinator, OPT_RECIPE_TYPE, "Recepttype", RECIPE_TYPE_OPTIONS, "dinner"),
    ])


class DinnerGenieSelect(SelectEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, option_key: str, name: str, options: list[str], default: str) -> None:
        self.coordinator = coordinator
        self.option_key = option_key
        self.default = default
        self._attr_name = name
        self._attr_options = options
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{option_key}"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.coordinator.entry.entry_id)}, "name": "Dinner Genie"}

    @property
    def current_option(self) -> str:
        return self.coordinator.entry.options.get(self.option_key, self.default)

    async def async_select_option(self, option: str) -> None:
        if option not in self.options:
            return
        await self.coordinator.async_update_option(self.option_key, option)
