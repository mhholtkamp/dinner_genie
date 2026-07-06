from __future__ import annotations

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DinnerGenieShoppingTodo(coordinator)])


class DinnerGenieShoppingTodo(CoordinatorEntity, TodoListEntity):
    _attr_has_entity_name = True
    _attr_name = "Boodschappen"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_shopping_todo"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.coordinator.entry.entry_id)}, "name": "Dinner Genie"}

    @property
    def todo_items(self) -> list[TodoItem]:
        lines = (self.coordinator.data or {}).get("shopping_lines") or []
        return [TodoItem(summary=str(line), status=TodoItemStatus.NEEDS_ACTION) for line in lines]
