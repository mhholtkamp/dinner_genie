from __future__ import annotations

DOMAIN = "dinner_genie"

CONF_BASE_URL = "base_url"
CONF_GROUP_ID = "group_id"
CONF_API_KEY = "api_key"

DEFAULT_BASE_URL = "https://dinner-genie.vercel.app/api"
DEFAULT_SCAN_INTERVAL_HOURS = 6

PLATFORMS = ["sensor", "button", "todo"]

HELPER_DAYS = "input_number.dinner_genie_aantal_dagen"
HELPER_SERVINGS = "input_number.dinner_genie_aantal_personen"

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = "dinner_genie_week_plan"
