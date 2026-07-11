from __future__ import annotations

from uuid import uuid4

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
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
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
    )

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_shopping_todo"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.coordinator.entry.entry_id)}, "name": "Savelio"}

    @property
    def todo_items(self) -> list[TodoItem]:
        items = (self.coordinator.data or {}).get("shopping_items") or []
        return [
            TodoItem(
                uid=str(item.get("uid")),
                summary=str(item.get("summary", "")),
                status=item.get("status", TodoItemStatus.NEEDS_ACTION),
            )
            for item in items
            if item.get("summary")
        ]

    async def async_create_todo_item(self, item: TodoItem) -> None:
        data = dict(self.coordinator.data or {})
        items = list(data.get("shopping_items") or [])
        items.append(
            {
                "uid": item.uid or str(uuid4()),
                "summary": item.summary,
                "status": item.status or TodoItemStatus.NEEDS_ACTION,
            }
        )
        data["shopping_items"] = items
        data["shopping_lines"] = [entry["summary"] for entry in items]
        self.coordinator.async_set_updated_data(data)
        self.async_update_listeners()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        data = dict(self.coordinator.data or {})
        items = list(data.get("shopping_items") or [])

        for index, entry in enumerate(items):
            if str(entry.get("uid")) == str(item.uid):
                items[index] = {
                    "uid": entry.get("uid"),
                    "summary": item.summary,
                    "status": item.status,
                }
                break

        data["shopping_items"] = items
        data["shopping_lines"] = [entry["summary"] for entry in items]
        self.coordinator.async_set_updated_data(data)
        self.async_update_listeners()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        uid_set = {str(uid) for uid in uids}
        data = dict(self.coordinator.data or {})
        items = [
            item
            for item in list(data.get("shopping_items") or [])
            if str(item.get("uid")) not in uid_set
        ]
        data["shopping_items"] = items
        data["shopping_lines"] = [entry["summary"] for entry in items]
        self.coordinator.async_set_updated_data(data)
        self.async_update_listeners()
