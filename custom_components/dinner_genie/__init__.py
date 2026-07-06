from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DinnerGenieClient
from .const import CONF_API_KEY, CONF_BASE_URL, CONF_GROUP_ID, DOMAIN, PLATFORMS
from .coordinator import DinnerGenieCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = DinnerGenieClient(
        session=session,
        base_url=entry.data[CONF_BASE_URL],
        group_id=entry.data[CONF_GROUP_ID],
        api_key=entry.data[CONF_API_KEY],
    )

    coordinator = DinnerGenieCoordinator(hass, client, entry.entry_id)
    await coordinator.async_load_stored_data()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
