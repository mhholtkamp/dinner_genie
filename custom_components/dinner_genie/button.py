from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[ButtonEntity] = [
        DinnerGenieGenerateWeekMenuButton(coordinator),
        DinnerGenieRandomButton(coordinator),
    ]
    async_add_entities(entities)


class DinnerGenieBaseButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator) -> None:
        self.coordinator = coordinator

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.coordinator.entry.entry_id)}, "name": "Savelio"}


class DinnerGenieGenerateWeekMenuButton(DinnerGenieBaseButton):
    _attr_name = "Vernieuw weekplanning"
    _attr_icon = "mdi:calendar-refresh"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_generate_weekmenu"

    async def async_press(self) -> None:
        await self.coordinator.async_generate_week_plan()


class DinnerGenieRandomButton(DinnerGenieBaseButton):
    _attr_name = "Kies willekeurig gerecht"
    _attr_icon = "mdi:dice-5"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_random_recipe"

    async def async_press(self) -> None:
        await self.coordinator.async_choose_random_recipe()
