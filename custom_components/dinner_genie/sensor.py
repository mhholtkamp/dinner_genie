from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        DinnerGenieRecipeCountSensor(coordinator),
        DinnerGenieRandomRecipeSensor(coordinator),
        DinnerGenieWeekMenuSensor(coordinator),
    ])


class DinnerGenieBaseSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.coordinator.entry.entry_id)}, "name": "Dinner Genie"}


class DinnerGenieRecipeCountSensor(DinnerGenieBaseSensor):
    _attr_name = "Aantal recepten"
    _attr_native_unit_of_measurement = "recepten"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_recipe_count"

    @property
    def native_value(self):
        recipes = (self.coordinator.data or {}).get("recipes") or {}
        return recipes.get("count", len(recipes.get("recipes", []) or []))


class DinnerGenieRandomRecipeSensor(DinnerGenieBaseSensor):
    _attr_name = "Willekeurig gerecht"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_random_recipe_sensor"

    @property
    def native_value(self):
        data = (self.coordinator.data or {}).get("random") or {}
        recipe = data.get("recipe") or {}
        return recipe.get("name") or "Geen gerecht gekozen"

    @property
    def extra_state_attributes(self):
        data = (self.coordinator.data or {}).get("random") or {}
        return {"recipe": data.get("recipe"), "pool_size": data.get("poolSize")}


class DinnerGenieWeekMenuSensor(DinnerGenieBaseSensor):
    _attr_name = "Weekmenu"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_weekmenu_sensor"

    @property
    def native_value(self):
        meals = (self.coordinator.data or {}).get("meals") or []
        return f"{len(meals)} gerechten" if meals else "Geen weekmenu"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        meals = data.get("meals") or []
        return {
            "meals": meals,
            "meal_names": [meal.get("name") for meal in meals if isinstance(meal, dict)],
            "shopping_lines": data.get("shopping_lines") or [],
        }
