from __future__ import annotations

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import entity_registry as er

from .api import DinnerGenieClient
from .const import CONF_BASE_URL, CONF_GROUP_ID, DEFAULT_DAYS, DEFAULT_SERVINGS, DOMAIN, OPT_DAYS, OPT_SERVINGS, PLATFORMS
from .coordinator import DinnerGenieCoordinator


async def _async_register_static_assets(hass: HomeAssistant) -> None:
    """Register Savelio static assets and Lovelace resources."""
    registered_key = f"{DOMAIN}_static_assets_registered"
    if hass.data.get(registered_key):
        return

    integration_path = Path(__file__).parent
    assets_path = integration_path / "assets"
    www_path = integration_path / "www"
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(f"/api/{DOMAIN}/assets", str(assets_path), False),
            StaticPathConfig(f"/api/{DOMAIN}/www", str(www_path), False),
        ]
    )
    hass.data[registered_key] = True


def _async_remove_legacy_day_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove obsolete per-day entities from older Savelio/Dinner Genie versions."""
    registry = er.async_get(hass)
    legacy_unique_ids = set()
    legacy_entity_ids = set()

    for day in range(1, 8):
        legacy_unique_ids.update(
            {
                f"{entry.entry_id}_day_{day}",
                f"{entry.entry_id}_replace_day_{day}",
                f"{entry.entry_id}_day_{day}_replace",
                f"{entry.entry_id}_replace_weekmenu_day_{day}",
            }
        )
        legacy_entity_ids.update(
            {
                f"sensor.{DOMAIN}_dag_{day}",
                f"button.{DOMAIN}_vervang_dag_{day}",
                f"button.{DOMAIN}_replace_day_{day}",
            }
        )

    for entity in list(registry.entities.values()):
        if entity.config_entry_id != entry.entry_id:
            continue
        if entity.unique_id in legacy_unique_ids or entity.entity_id in legacy_entity_ids:
            registry.async_remove(entity.entity_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await _async_register_static_assets(hass)
    _async_remove_legacy_day_entities(hass, entry)
    session = async_get_clientsession(hass)
    client = DinnerGenieClient(
        session,
        entry.data[CONF_BASE_URL],
        entry.data[CONF_GROUP_ID],
        entry.data[CONF_API_KEY],
    )

    hass.data.setdefault(DOMAIN, {})
    coordinator = DinnerGenieCoordinator(hass, entry, client)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    if OPT_DAYS not in entry.options or OPT_SERVINGS not in entry.options:
        hass.config_entries.async_update_entry(
            entry,
            options={
                OPT_DAYS: entry.options.get(OPT_DAYS, DEFAULT_DAYS),
                OPT_SERVINGS: entry.options.get(OPT_SERVINGS, DEFAULT_SERVINGS),
                **entry.options,
            },
        )

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
