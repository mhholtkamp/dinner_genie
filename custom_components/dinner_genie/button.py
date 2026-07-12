from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

SEND_SHOPPING_ENTITY_ID = "button.dinner_genie_stuur_boodschappen_naar_ha_lijst"
CLEAR_SHOPPING_ENTITY_ID = "button.dinner_genie_leeg_savelio_boodschappenlijst"
SEND_AND_CLEAR_SHOPPING_ENTITY_ID = "button.dinner_genie_stuur_boodschappen_naar_ha_en_leeg_savelio"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[ButtonEntity] = [
        DinnerGenieRefreshDataButton(coordinator),
        DinnerGenieGenerateWeekMenuButton(coordinator),
        DinnerGenieRandomButton(coordinator),
        DinnerGenieSendShoppingListButton(coordinator),
        DinnerGenieClearShoppingListButton(coordinator),
        DinnerGenieSendAndClearShoppingListButton(coordinator),
    ]
    async_add_entities(entities)


class DinnerGenieBaseButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator) -> None:
        self.coordinator = coordinator

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.coordinator.entry.entry_id)}, "name": "Savelio"}


class DinnerGenieRefreshDataButton(DinnerGenieBaseButton):
    _attr_name = "Update gegevens"
    _attr_icon = "mdi:cloud-refresh"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_refresh_data"

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()


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


class DinnerGenieSendShoppingListButton(DinnerGenieBaseButton):
    _attr_name = "Stuur boodschappen naar HA lijst"
    _attr_icon = "mdi:cart-arrow-right"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_send_shopping_to_ha_list"
        self._attr_entity_id = SEND_SHOPPING_ENTITY_ID

    @property
    def available(self) -> bool:
        return True

    async def async_press(self) -> None:
        await self.coordinator.async_send_shopping_to_ha()


class DinnerGenieClearShoppingListButton(DinnerGenieBaseButton):
    _attr_name = "Leeg Savelio boodschappenlijst"
    _attr_icon = "mdi:cart-remove"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_clear_shopping_list"
        self._attr_entity_id = CLEAR_SHOPPING_ENTITY_ID

    @property
    def available(self) -> bool:
        return True

    async def async_press(self) -> None:
        await self.coordinator.async_clear_shopping_list()


class DinnerGenieSendAndClearShoppingListButton(DinnerGenieBaseButton):
    _attr_name = "Stuur boodschappen naar HA en leeg Savelio"
    _attr_icon = "mdi:cart-check"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_send_and_clear_shopping_list"
        self._attr_entity_id = SEND_AND_CLEAR_SHOPPING_ENTITY_ID

    @property
    def available(self) -> bool:
        return True

    async def async_press(self) -> None:
        await self.coordinator.async_send_shopping_to_ha()
        await self.coordinator.async_clear_shopping_list()
