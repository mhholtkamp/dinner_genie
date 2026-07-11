from __future__ import annotations

DOMAIN = "dinner_genie"

CONF_BASE_URL = "base_url"
CONF_GROUP_ID = "group_id"
CONF_API_KEY = "api_key"

DEFAULT_BASE_URL = "https://savelio.vercel.app/api"

PLATFORMS = ["sensor", "button", "number", "todo", "select"]

OPT_DAYS = "days"
OPT_SERVINGS = "servings"
OPT_DIET_TYPE = "diet_type"
OPT_RECIPE_TYPE = "recipe_type"

DEFAULT_DAYS = 5
DEFAULT_SERVINGS = 4
MIN_DAYS = 1
MAX_DAYS = 7
MIN_SERVINGS = 1
MAX_SERVINGS = 50

DIET_OPTIONS = ["all", "vegetarian", "vegan"]
RECIPE_TYPE_OPTIONS = ["dinner", "breakfast", "baking", "lunch", "snack", "other"]

PLACEHOLDER_IMAGE_URL = f"/api/{DOMAIN}/assets/placeholder_recipe.png"
