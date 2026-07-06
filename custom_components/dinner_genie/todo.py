from __future__ import annotations

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DinnerGenieShoppingList(coordinator, entry.entry_id)])


class DinnerGenieShoppingList(CoordinatorEntity, TodoListEntity):
    _attr_name = "Dinner Genie boodschappenlijst"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_shopping_list"

    @property
    def todo_items(self) -> list[TodoItem]:
        lines = self.coordinator.data.get("shopping_lines", []) if self.coordinator.data else []
        return [
            TodoItem(
                summary=str(line),
                status=TodoItemStatus.NEEDS_ACTION,
            )
            for line in lines
        ]
