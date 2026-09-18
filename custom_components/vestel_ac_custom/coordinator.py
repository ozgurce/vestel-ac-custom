"""Data coordinator for Vestel AC Custom."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    MODE_ALIASES,
    VestelAcApiError,
    VestelAcClient,
    normalize_fan_speed,
    normalize_horizontal_swing_display,
    normalize_swing,
)
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

    def async_apply_optimistic_update(self, changes: dict[str, Any]) -> None:
        """Reflect a successfully sent command immediately while the cloud catches up."""
        data = dict(self.data or {})
        if "mode" in changes:
            mode = _normalize_mode(changes["mode"])
            if mode == "off":
                data["power_state"] = "off"
            elif mode:
                data["mode"] = mode
                data["power_state"] = "on"
        if "temperature" in changes and changes["temperature"] is not None:
            data["target_temperature"] = max(16, min(30, int(float(changes["temperature"]))))
        if "fan_speed" in changes and changes["fan_speed"] is not None:
            data["fan_speed"] = normalize_fan_speed(changes["fan_speed"])
        if "vertical_swing" in changes and changes["vertical_swing"] is not None:
            data["vertical_swing"] = normalize_swing(changes["vertical_swing"], "vertical swing")
        if "horizontal_swing" in changes and changes["horizontal_swing"] is not None:
            data["horizontal_swing"] = normalize_horizontal_swing_display(changes["horizontal_swing"])
        for key in ("turbo", "eco", "sleep"):
            if key in changes and changes[key] is not None:
                data[key] = bool(changes[key])
        self.async_set_updated_data(data)

    def async_schedule_follow_up_refreshes(self, delays: tuple[int, ...]) -> None:
        """Schedule short follow-up polls after a command."""
        for delay in delays:
            self.hass.async_create_task(self._async_delayed_refresh(delay))

    async def _async_delayed_refresh(self, delay: int) -> None:
        await asyncio.sleep(delay)
        await self.async_request_refresh()


def _normalize_mode(value: Any) -> str | None:
    key = str(value or "").strip().lower()
    return MODE_ALIASES.get(key, key) or None
