from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            DinnerGenieRecipeCountSensor(coordinator, entry.entry_id),
            DinnerGenieRandomRecipeSensor(coordinator, entry.entry_id),
            DinnerGenieWeekMenuSensor(coordinator, entry.entry_id),
        ]
    )


class DinnerGenieBaseSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id


class DinnerGenieRecipeCountSensor(DinnerGenieBaseSensor):
    _attr_name = "Dinner Genie aantal recepten"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_recipe_count"

    @property
    def native_value(self) -> int:
        recipes = self.coordinator.data.get("recipes", {}) if self.coordinator.data else {}
        return int(recipes.get("count", len(recipes.get("recipes", []))))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        recipes = self.coordinator.data.get("recipes", {}) if self.coordinator.data else {}
        return {"group": recipes.get("group"), "recipes": recipes.get("recipes", [])}


class DinnerGenieRandomRecipeSensor(DinnerGenieBaseSensor):
    _attr_name = "Dinner Genie willekeurig gerecht"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_random_recipe"

    @property
    def native_value(self) -> str | None:
        random_data = self.coordinator.data.get("random", {}) if self.coordinator.data else {}
        recipe = random_data.get("recipe") or {}
        return recipe.get("name")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        random_data = self.coordinator.data.get("random", {}) if self.coordinator.data else {}
        return {
            "pool_size": random_data.get("poolSize"),
            "recipe": random_data.get("recipe"),
        }


class DinnerGenieWeekMenuSensor(DinnerGenieBaseSensor):
    _attr_name = "Dinner Genie weekmenu"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_week_menu"

    @property
    def native_value(self) -> str:
        meals = self.coordinator.data.get("meals", []) if self.coordinator.data else []
        if not meals:
            return "Geen weekmenu"
        return f"{len(meals)} maaltijden"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        week_plan = self.coordinator.data.get("week_plan", {}) if self.coordinator.data else {}
        meals = self.coordinator.data.get("meals", []) if self.coordinator.data else []
        return {
            "days": week_plan.get("days"),
            "servings": week_plan.get("servings"),
            "meals": meals,
            "meal_names": [meal.get("name") for meal in meals if isinstance(meal, dict)],
            "shopping_lines": self.coordinator.data.get("shopping_lines", []) if self.coordinator.data else [],
        }
