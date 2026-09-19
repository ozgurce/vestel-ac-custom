"""Vestel AC Custom integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import VestelAcClient, VestelAcConfig
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
    PLATFORMS,
)
from .coordinator import VestelAcCoordinator


VestelConfigEntry = ConfigEntry


def _entry_config(entry: ConfigEntry) -> VestelAcConfig:
    data = entry.data
    return VestelAcConfig(
        email=data[CONF_EMAIL],
        password=data[CONF_PASSWORD],
        region=data.get(CONF_REGION, DEFAULT_REGION),
        user_pool_id=data.get(CONF_USER_POOL_ID, DEFAULT_USER_POOL_ID),
        app_client_id=data.get(CONF_APP_CLIENT_ID, DEFAULT_APP_CLIENT_ID),
        app_client_secret=data.get(CONF_APP_CLIENT_SECRET, ""),
        rest_base_url=data.get(CONF_REST_BASE_URL, DEFAULT_REST_BASE_URL),
        thing_name=data[CONF_THING_NAME],
        home_id=data.get(CONF_HOME_ID, ""),
        product_line=data.get(CONF_PRODUCT_LINE, DEFAULT_PRODUCT_LINE),
        device_kind=data.get(CONF_DEVICE_KIND, DEFAULT_DEVICE_KIND),
        command_topic=data.get(CONF_COMMAND_TOPIC, ""),
    )


async def async_setup_entry(hass: HomeAssistant, entry: VestelConfigEntry) -> bool:
    """Set up Vestel AC Custom from a config entry."""
    session = async_get_clientsession(hass)
    api = VestelAcClient(session, _entry_config(entry))
    scan_interval = int(entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    coordinator = VestelAcCoordinator(
        hass,
        api,
        timedelta(seconds=max(15, min(scan_interval, DEFAULT_SCAN_INTERVAL))),
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: VestelConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: VestelConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
