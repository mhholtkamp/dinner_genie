from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DinnerGenieClient
from .const import CONF_BASE_URL, CONF_GROUP_ID, DEFAULT_DAYS, DEFAULT_SERVINGS, DOMAIN, OPT_DAYS, OPT_SERVINGS, PLATFORMS
from .coordinator import DinnerGenieCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
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
