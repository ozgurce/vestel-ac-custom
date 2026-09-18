"""Climate platform for Vestel AC Custom."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_THING_NAME,
    DOMAIN,
    SERVICE_SET_ECO,
    SERVICE_SET_SLEEP,
    SERVICE_SET_TURBO,
)
from .coordinator import VestelAcCoordinator

HVAC_TO_VESTEL = {
    HVACMode.OFF: "off",
    HVACMode.AUTO: "auto",
    HVACMode.COOL: "cool",
    HVACMode.DRY: "dry",
    HVACMode.FAN_ONLY: "fan",
    HVACMode.HEAT: "heat",
}

VESTEL_TO_HVAC = {
    "off": HVACMode.OFF,
    "auto": HVACMode.AUTO,
    "cool": HVACMode.COOL,
    "dry": HVACMode.DRY,
    "fan": HVACMode.FAN_ONLY,
    "heat": HVACMode.HEAT,
}

FAN_MODES = ["Auto", "Speed1", "Speed2", "Speed3", "Speed4", "Speed5"]
SWING_MODES = ["Off", "Pos1", "Pos2", "Pos3", "Pos4", "Pos5", "Pos6"]
_SERVICES_REGISTERED = False


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    """Set up Vestel AC climate entity."""
    global _SERVICES_REGISTERED
    coordinator: VestelAcCoordinator = entry.runtime_data
    async_add_entities([VestelAcClimate(coordinator, entry)])

    if _SERVICES_REGISTERED:
        return
    platform = entity_platform.async_get_current_platform()
    service_schema = {vol.Required("enabled"): cv.boolean}
    platform.async_register_entity_service(SERVICE_SET_TURBO, service_schema, "async_set_turbo")
    platform.async_register_entity_service(SERVICE_SET_ECO, service_schema, "async_set_eco")
    platform.async_register_entity_service(SERVICE_SET_SLEEP, service_schema, "async_set_sleep")
    _SERVICES_REGISTERED = True


class VestelAcClimate(CoordinatorEntity[VestelAcCoordinator], ClimateEntity):
    """Vestel AC climate entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 16
    _attr_max_temp = 30
    _attr_target_temperature_step = 1
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.AUTO,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
    ]
    _attr_fan_modes = FAN_MODES
    _attr_swing_modes = SWING_MODES
    _attr_swing_horizontal_modes = SWING_MODES
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.SWING_HORIZONTAL_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: VestelAcCoordinator, entry) -> None:
        super().__init__(coordinator)
        thing_name = entry.data[CONF_THING_NAME]
        self._attr_unique_id = thing_name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, thing_name)},
            manufacturer="Vestel",
            name="Vestel AC",
            model=entry.data.get("product_line", "AC"),
        )

    @property
    def available(self) -> bool:
        return super().available and bool(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "turbo": data.get("turbo"),
            "eco": data.get("eco"),
            "sleep": data.get("sleep"),
            "wifi_rssi": data.get("wifi_rssi"),
            "current_mode": data.get("current_mode"),
        }

    @property
    def current_temperature(self) -> float | None:
        return _as_float((self.coordinator.data or {}).get("room_temperature"))

    @property
    def target_temperature(self) -> float | None:
        return _as_float((self.coordinator.data or {}).get("target_temperature"))

    @property
    def hvac_mode(self) -> HVACMode:
        data = self.coordinator.data or {}
        if data.get("power_state") == "off":
            return HVACMode.OFF
        return VESTEL_TO_HVAC.get(str(data.get("mode") or "").lower(), HVACMode.AUTO)

    @property
    def fan_mode(self) -> str | None:
        return (self.coordinator.data or {}).get("fan_speed")

    @property
    def swing_mode(self) -> str | None:
        return (self.coordinator.data or {}).get("vertical_swing")

    @property
    def swing_horizontal_mode(self) -> str | None:
        return (self.coordinator.data or {}).get("horizontal_swing")

    async def _send(self, **kwargs: Any) -> None:
        await self.coordinator.api.async_command(**kwargs)
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        await self._send(mode=HVAC_TO_VESTEL[hvac_mode])

    async def async_turn_on(self) -> None:
        mode = (self.coordinator.data or {}).get("mode") or "auto"
        if mode == "off":
            mode = "auto"
        await self._send(mode=mode)

    async def async_turn_off(self) -> None:
        await self._send(mode="off")

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self._send(temperature=temperature)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        await self._send(fan_speed=fan_mode)

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        await self._send(vertical_swing=swing_mode)

    async def async_set_swing_horizontal_mode(self, swing_horizontal_mode: str) -> None:
        await self._send(horizontal_swing=swing_horizontal_mode)

    async def async_set_turbo(self, enabled: bool) -> None:
        await self._send(turbo=enabled)

    async def async_set_eco(self, enabled: bool) -> None:
        await self._send(eco=enabled)

    async def async_set_sleep(self, enabled: bool) -> None:
        await self._send(sleep=enabled)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
