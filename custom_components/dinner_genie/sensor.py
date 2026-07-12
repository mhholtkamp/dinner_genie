from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PLACEHOLDER_IMAGE_URL


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        DinnerGenieRecipeCountSensor(coordinator),
        DinnerGenieAllRecipesSensor(coordinator),
        DinnerGenieRandomRecipeSensor(coordinator),
        DinnerGenieWeekMenuSensor(coordinator),
    ]
    async_add_entities(entities)


class DinnerGenieBaseSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.coordinator.entry.entry_id)}, "name": "Savelio"}


def _format_amount(amount: Any) -> str | None:
    if amount in (None, ""):
        return None
    if isinstance(amount, float) and amount.is_integer():
        return str(int(amount))
    return str(amount)


def _format_ingredient(ingredient: dict[str, Any]) -> str:
    amount = _format_amount(ingredient.get("amount"))
    unit = ingredient.get("unit")
    name = ingredient.get("name") or ""

    parts = []
    if amount:
        parts.append(amount)
    if unit:
        parts.append(str(unit))
    if name:
        parts.append(str(name))

    return " ".join(parts).strip()


def _format_ingredients(ingredients_v2: Any, fallback: Any) -> list[str]:
    if isinstance(ingredients_v2, list) and ingredients_v2:
        formatted = [
            _format_ingredient(item)
            for item in ingredients_v2
            if isinstance(item, dict) and _format_ingredient(item)
        ]
        if formatted:
            return formatted

    if isinstance(fallback, list):
        return [str(item) for item in fallback if item]

    return []


def _markdown_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _recipe_attributes(recipe: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(recipe, dict) or not recipe:
        return {}

    ingredients_v2 = recipe.get("ingredientsV2") or recipe.get("ingredients_v2") or []
    ingredients_raw = recipe.get("ingredients") or []
    ingredients_formatted = _format_ingredients(ingredients_v2, ingredients_raw)
    image_url = recipe.get("imageUrl") or recipe.get("image_url") or recipe.get("displayImage") or recipe.get("display_image") or PLACEHOLDER_IMAGE_URL

    return {
        "recipe_id": recipe.get("id") or recipe.get("recipe_id") or recipe.get("recipeId"),
        "name": recipe.get("name"),
        "description": recipe.get("description"),
        "image_url": image_url,
        "display_image": image_url,
        "has_recipe_image": bool(recipe.get("imageUrl") or recipe.get("image_url") or recipe.get("displayImage") or recipe.get("display_image")),
        "prep_time": recipe.get("prepTime") or recipe.get("prep_time"),
        "category": recipe.get("category"),
        "recipe_type": recipe.get("recipeType") or recipe.get("recipe_type"),
        "diet_type": recipe.get("dietType") or recipe.get("diet_type"),
        "servings": recipe.get("servings"),
        "ingredients": ingredients_raw,
        "ingredients_v2": ingredients_v2,
        "ingredients_formatted": ingredients_formatted,
        "ingredients_markdown": _markdown_list(ingredients_formatted),
        "instructions": recipe.get("instructions"),
        "created_at": recipe.get("createdAt"),
        "group_id": recipe.get("groupId"),
        "planning_day": recipe.get("planning_day"),
        "planning_date": recipe.get("planning_date"),
        "planning_weekday": recipe.get("planning_weekday"),
        "planning_label": recipe.get("planning_label"),
        "planning_is_past": bool(recipe.get("planning_is_past")),
    }


def _recipes_for_dashboard(recipes: Any) -> list[dict[str, Any]]:
    if not isinstance(recipes, list):
        return []

    result: list[dict[str, Any]] = []
    for recipe in recipes:
        if not isinstance(recipe, dict):
            continue
        result.append(_recipe_attributes(recipe))
    return result


def _day_entry_for_dashboard(entry: Any) -> dict[str, Any] | None:
    if not isinstance(entry, dict):
        return None

    recipe = _recipe_attributes(entry.get("recipe"))
    day = entry.get("day") or recipe.get("planning_day")
    date = entry.get("date") or recipe.get("planning_date")
    weekday = entry.get("weekday") or recipe.get("planning_weekday")
    label = entry.get("label") or recipe.get("planning_label")
    is_past = bool(entry.get("is_past") or recipe.get("planning_is_past"))

    recipe["planning_day"] = day
    recipe["planning_date"] = date
    recipe["planning_weekday"] = weekday
    recipe["planning_label"] = label
    recipe["planning_is_past"] = is_past

    return {
        "day": day,
        "date": date,
        "weekday": weekday,
        "label": label,
        "is_past": is_past,
        "recipe": recipe,
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

    @property
    def extra_state_attributes(self):
        recipes = (self.coordinator.data or {}).get("recipes") or {}
        recipe_list = recipes.get("recipes", []) or []
        return {"recipes": _recipes_for_dashboard(recipe_list)}


class DinnerGenieAllRecipesSensor(DinnerGenieBaseSensor):
    _attr_name = "Recepten"
    _attr_icon = "mdi:book-open-variant"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_all_recipes"

    @property
    def native_value(self):
        recipes = (self.coordinator.data or {}).get("recipes") or {}
        count = recipes.get("count", len(recipes.get("recipes", []) or []))
        return f"{count} recepten"

    @property
    def extra_state_attributes(self):
        recipes = (self.coordinator.data or {}).get("recipes") or {}
        recipe_list = recipes.get("recipes", []) or []
        return {
            "count": recipes.get("count", len(recipe_list)),
            "recipes": _recipes_for_dashboard(recipe_list),
        }


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
        day_entries = data.get("day_entries") or []
        dashboard_days = [
            item
            for item in (_day_entry_for_dashboard(entry) for entry in day_entries)
            if item
        ]
        dashboard_meals = _recipes_for_dashboard(meals)
        return {
            "meals": dashboard_meals,
            "days": dashboard_days,
            "meal_names": [meal.get("name") for meal in dashboard_meals if isinstance(meal, dict)],
            "shopping_lines": data.get("shopping_lines") or [],
        }
