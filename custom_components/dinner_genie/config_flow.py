from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DinnerGenieApiError, DinnerGenieClient
from .const import CONF_API_KEY, CONF_BASE_URL, CONF_GROUP_ID, DEFAULT_BASE_URL, DOMAIN


class DinnerGenieConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].rstrip("/")
            group_id = user_input[CONF_GROUP_ID].strip()
            api_key = user_input[CONF_API_KEY].strip()

            client = DinnerGenieClient(
                async_get_clientsession(self.hass),
                base_url,
                group_id,
                api_key,
            )

            try:
                await client.async_test_connection()
            except DinnerGenieApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(group_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Dinner Genie",
                    data={
                        CONF_BASE_URL: base_url,
                        CONF_GROUP_ID: group_id,
                        CONF_API_KEY: api_key,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
                vol.Required(CONF_GROUP_ID): str,
                vol.Required(CONF_API_KEY): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
