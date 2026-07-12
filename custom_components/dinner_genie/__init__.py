from __future__ import annotations

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import entity_registry as er

from .api import DinnerGenieClient
from .const import (
    CONF_BASE_URL,
    CONF_GROUP_ID,
    DEFAULT_DAYS,
    DEFAULT_REFRESH_INTERVAL_HOURS,
    DEFAULT_SERVINGS,
    DOMAIN,
    OPT_DAYS,
    OPT_REFRESH_INTERVAL_HOURS,
    OPT_SERVINGS,
    PLATFORMS,
)
from .coordinator import DinnerGenieCoordinator

SERVICE_SEND_SHOPPING_TO_HA_AND_CLEAR = "send_shopping_to_ha_and_clear"


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


def _async_reset_shopping_buttons(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove stale shopping button registry entries so they can be recreated."""
    registry = er.async_get(hass)
    known_unique_ids = {
        f"{entry.entry_id}_send_shopping_to_ha_list",
        f"{entry.entry_id}_shopping_export_to_ha_list",
        f"{entry.entry_id}_clear_shopping_list",
        f"{entry.entry_id}_send_and_clear_shopping_list",
    }
    known_entity_ids = {
        "button.dinner_genie_stuur_boodschappen_naar_ha_lijst",
        "button.savelio_stuur_boodschappen_naar_ha_lijst",
        "button.dinner_genie_send_shopping_to_ha_list",
        "button.savelio_send_shopping_to_ha_list",
        "button.dinner_genie_leeg_savelio_boodschappenlijst",
        "button.savelio_leeg_savelio_boodschappenlijst",
        "button.dinner_genie_clear_shopping_list",
        "button.savelio_clear_shopping_list",
        "button.dinner_genie_stuur_boodschappen_naar_ha_en_leeg_savelio",
        "button.savelio_stuur_boodschappen_naar_ha_en_leeg_savelio",
        "button.dinner_genie_send_and_clear_shopping_list",
        "button.savelio_send_and_clear_shopping_list",
    }

    for entity in list(registry.entities.values()):
        if not entity.entity_id.startswith("button."):
            continue
        if entity.config_entry_id not in (None, entry.entry_id):
            continue
        if entity.unique_id in known_unique_ids or entity.entity_id in known_entity_ids:
            registry.async_remove(entity.entity_id)


def _coordinator_for_service(hass: HomeAssistant, call: ServiceCall) -> DinnerGenieCoordinator:
    coordinators = hass.data.get(DOMAIN, {})
    entry_id = call.data.get("entry_id")

    if entry_id:
        coordinator = coordinators.get(entry_id)
        if coordinator:
            return coordinator
        raise HomeAssistantError(f"Savelio configuratie niet gevonden: {entry_id}")

    if len(coordinators) == 1:
        return next(iter(coordinators.values()))

    if not coordinators:
        raise HomeAssistantError("Geen Savelio configuratie gevonden.")

    raise HomeAssistantError("Meerdere Savelio configuraties gevonden. Geef entry_id mee.")


def _async_register_services(hass: HomeAssistant) -> None:
    registered_key = f"{DOMAIN}_services_registered"
    if hass.data.get(registered_key):
        return

    async def async_send_shopping_to_ha_and_clear(call: ServiceCall) -> None:
        coordinator = _coordinator_for_service(hass, call)
        await coordinator.async_send_shopping_to_ha()
        await coordinator.async_clear_shopping_list()

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_SHOPPING_TO_HA_AND_CLEAR,
        async_send_shopping_to_ha_and_clear,
    )
    hass.data[registered_key] = True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await _async_register_static_assets(hass)
    _async_remove_legacy_day_entities(hass, entry)
    _async_reset_shopping_buttons(hass, entry)
    session = async_get_clientsession(hass)
    client = DinnerGenieClient(
        session,
        entry.data[CONF_BASE_URL],
        entry.data[CONF_GROUP_ID],
        entry.data[CONF_API_KEY],
    )

    hass.data.setdefault(DOMAIN, {})
    _async_register_services(hass)
    coordinator = DinnerGenieCoordinator(hass, entry, client)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    if (
        OPT_DAYS not in entry.options
        or OPT_SERVINGS not in entry.options
        or OPT_REFRESH_INTERVAL_HOURS not in entry.options
    ):
        hass.config_entries.async_update_entry(
            entry,
            options={
                OPT_DAYS: entry.options.get(OPT_DAYS, DEFAULT_DAYS),
                OPT_SERVINGS: entry.options.get(OPT_SERVINGS, DEFAULT_SERVINGS),
                OPT_REFRESH_INTERVAL_HOURS: entry.options.get(
                    OPT_REFRESH_INTERVAL_HOURS,
                    DEFAULT_REFRESH_INTERVAL_HOURS,
                ),
                **entry.options,
            },
        )

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
