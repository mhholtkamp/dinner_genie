from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MAX_DAYS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[ButtonEntity] = [
        DinnerGenieGenerateWeekMenuButton(coordinator),
        DinnerGenieRandomButton(coordinator),
    ]
    entities.extend(DinnerGenieReplaceDayButton(coordinator, day_number) for day_number in range(1, MAX_DAYS + 1))
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


class DinnerGenieReplaceDayButton(DinnerGenieBaseButton):
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator, day_number: int) -> None:
        super().__init__(coordinator)
        self.day_number = day_number
        self._attr_name = f"Vervang dag {day_number}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_replace_day_{day_number}"

    @property
    def available(self) -> bool:
        return False

    async def async_press(self) -> None:
        await self.coordinator.async_replace_day(self.day_number)
