"""Config flow for Vestel AC Custom."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import VestelAcApiError, VestelAcAuthError, VestelAcClient, VestelAcConfig
from .const import (
    CONF_APP_CLIENT_ID,
    CONF_APP_CLIENT_SECRET,
    CONF_COMMAND_TOPIC,
    CONF_DEVICE_KIND,
    CONF_HOME_ID,
    CONF_PRODUCT_LINE,
    CONF_REGION,
    CONF_REST_BASE_URL,
    CONF_SCAN_INTERVAL,
    CONF_THING_NAME,
    CONF_USER_POOL_ID,
    DEFAULT_APP_CLIENT_ID,
    DEFAULT_DEVICE_KIND,
    DEFAULT_PRODUCT_LINE,
    DEFAULT_REGION,
    DEFAULT_REST_BASE_URL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USER_POOL_ID,
    DOMAIN,
)


def _schema(user_input: dict[str, Any] | None = None) -> vol.Schema:
    data = user_input or {}
    return vol.Schema(
        {
            vol.Required(CONF_EMAIL, default=data.get(CONF_EMAIL, "")): str,
            vol.Required(CONF_PASSWORD, default=data.get(CONF_PASSWORD, "")): str,
            vol.Required(CONF_THING_NAME, default=data.get(CONF_THING_NAME, "")): str,
            vol.Required(CONF_HOME_ID, default=data.get(CONF_HOME_ID, "")): str,
            vol.Optional(CONF_PRODUCT_LINE, default=data.get(CONF_PRODUCT_LINE, DEFAULT_PRODUCT_LINE)): str,
            vol.Optional(CONF_DEVICE_KIND, default=data.get(CONF_DEVICE_KIND, DEFAULT_DEVICE_KIND)): str,
            vol.Optional(CONF_COMMAND_TOPIC, default=data.get(CONF_COMMAND_TOPIC, "")): str,
            vol.Optional(CONF_REST_BASE_URL, default=data.get(CONF_REST_BASE_URL, DEFAULT_REST_BASE_URL)): str,
            vol.Optional(CONF_REGION, default=data.get(CONF_REGION, DEFAULT_REGION)): str,
            vol.Optional(CONF_USER_POOL_ID, default=data.get(CONF_USER_POOL_ID, DEFAULT_USER_POOL_ID)): str,
            vol.Optional(CONF_APP_CLIENT_ID, default=data.get(CONF_APP_CLIENT_ID, DEFAULT_APP_CLIENT_ID)): str,
            vol.Optional(CONF_APP_CLIENT_SECRET, default=data.get(CONF_APP_CLIENT_SECRET, "")): str,
            vol.Optional(CONF_SCAN_INTERVAL, default=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): int,
        }
    )


def _to_config(user_input: dict[str, Any]) -> VestelAcConfig:
    return VestelAcConfig(
        email=user_input[CONF_EMAIL],
        password=user_input[CONF_PASSWORD],
        region=user_input.get(CONF_REGION, DEFAULT_REGION),
        user_pool_id=user_input.get(CONF_USER_POOL_ID, DEFAULT_USER_POOL_ID),
        app_client_id=user_input.get(CONF_APP_CLIENT_ID, DEFAULT_APP_CLIENT_ID),
        app_client_secret=user_input.get(CONF_APP_CLIENT_SECRET, ""),
        rest_base_url=user_input.get(CONF_REST_BASE_URL, DEFAULT_REST_BASE_URL),
        thing_name=user_input[CONF_THING_NAME],
        home_id=user_input.get(CONF_HOME_ID, ""),
        product_line=user_input.get(CONF_PRODUCT_LINE, DEFAULT_PRODUCT_LINE),
        device_kind=user_input.get(CONF_DEVICE_KIND, DEFAULT_DEVICE_KIND),
        command_topic=user_input.get(CONF_COMMAND_TOPIC, ""),
    )


async def _validate_input(hass: HomeAssistant, user_input: dict[str, Any]) -> None:
    session = async_get_clientsession(hass)
    api = VestelAcClient(session, _to_config(user_input))
    await api.async_login()
    await api.async_status()


class VestelAcConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Vestel AC Custom."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_THING_NAME])
            self._abort_if_unique_id_configured()
            try:
                await _validate_input(self.hass, user_input)
            except VestelAcAuthError:
                errors["base"] = "invalid_auth"
            except (VestelAcApiError, ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                title = f"Vestel AC {user_input[CONF_THING_NAME][-8:]}"
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input),
            errors=errors,
        )
