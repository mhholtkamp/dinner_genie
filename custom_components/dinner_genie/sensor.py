from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MAX_DAYS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        DinnerGenieRecipeCountSensor(coordinator),
        DinnerGenieRandomRecipeSensor(coordinator),
        DinnerGenieWeekMenuSensor(coordinator),
    ]
    entities.extend(DinnerGenieDayMealSensor(coordinator, day_number) for day_number in range(1, MAX_DAYS + 1))
    async_add_entities(entities)


class DinnerGenieBaseSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.coordinator.entry.entry_id)}, "name": "Dinner Genie"}


def _recipe_attributes(recipe: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(recipe, dict) or not recipe:
        return {}

    ingredients_v2 = recipe.get("ingredientsV2") or []
    ingredients = recipe.get("ingredients") or []

    return {
        "recipe_id": recipe.get("id"),
        "name": recipe.get("name"),
        "description": recipe.get("description"),
        "image_url": recipe.get("imageUrl"),
        "prep_time": recipe.get("prepTime"),
        "category": recipe.get("category"),
        "recipe_type": recipe.get("recipeType"),
        "diet_type": recipe.get("dietType"),
        "servings": recipe.get("servings"),
        "ingredients": ingredients,
        "ingredients_v2": ingredients_v2,
        "instructions": recipe.get("instructions"),
        "created_at": recipe.get("createdAt"),
        "group_id": recipe.get("groupId"),
    }


class DinnerGenieRecipeCountSensor(DinnerGenieBaseSensor):
    _attr_name = "Aantal recepten"
    _attr_native_unit_of_measurement = "recepten"
    _attr_icon = "mdi:silverware-fork-knife"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_recipe_count"

    @property
    def native_value(self):
        recipes = (self.coordinator.data or {}).get("recipes") or {}
        return recipes.get("count", len(recipes.get("recipes", []) or []))


class DinnerGenieRandomRecipeSensor(DinnerGenieBaseSensor):
    _attr_name = "Willekeurig gerecht"
    _attr_icon = "mdi:shuffle-variant"

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
        recipe = data.get("recipe") or {}
        return {"pool_size": data.get("poolSize"), **_recipe_attributes(recipe)}


class DinnerGenieWeekMenuSensor(DinnerGenieBaseSensor):
    _attr_name = "Weekmenu"
    _attr_icon = "mdi:calendar-week"

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


class DinnerGenieDayMealSensor(DinnerGenieBaseSensor):
    _attr_icon = "mdi:food"

    def __init__(self, coordinator, day_number: int) -> None:
        super().__init__(coordinator)
        self.day_number = day_number
        self._attr_name = f"Dag {day_number}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_day_{day_number}"

    @property
    def native_value(self):
        recipe = self._recipe
        if not recipe:
            return "Geen gerecht"
        return recipe.get("name") or "Onbekend gerecht"

    @property
    def available(self) -> bool:
        return super().available and self.day_number <= self.coordinator.days

    @property
    def extra_state_attributes(self):
        recipe = self._recipe
        attributes = _recipe_attributes(recipe)
        attributes["day"] = self.day_number
        return attributes

    @property
    def _recipe(self) -> dict[str, Any] | None:
        meals = (self.coordinator.data or {}).get("meals") or []
        index = self.day_number - 1
        if index >= len(meals):
            return None
        recipe = meals[index]
        return recipe if isinstance(recipe, dict) else None
