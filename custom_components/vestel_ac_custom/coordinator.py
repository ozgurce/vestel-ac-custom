"""Data coordinator for Vestel AC Custom."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import VestelAcApiError, VestelAcClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class VestelAcCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate Vestel AC polling."""

    def __init__(self, hass: HomeAssistant, api: VestelAcClient, update_interval: timedelta) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.async_status()
        except VestelAcApiError as err:
            raise UpdateFailed(str(err)) from err
