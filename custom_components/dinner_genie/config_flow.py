from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DinnerGenieApiError, DinnerGenieClient
from .const import CONF_BASE_URL, CONF_GROUP_ID, DEFAULT_BASE_URL, DOMAIN


class DinnerGenieConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = DinnerGenieClient(
                session,
                user_input[CONF_BASE_URL],
                user_input[CONF_GROUP_ID],
                user_input[CONF_API_KEY],
            )
            try:
                await client.validate()
            except DinnerGenieApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(user_input[CONF_GROUP_ID])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Savelio",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
                vol.Required(CONF_GROUP_ID): str,
                vol.Required(CONF_API_KEY): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
