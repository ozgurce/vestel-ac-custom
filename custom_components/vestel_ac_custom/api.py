"""Vestel HomeVSmart API client."""

from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urljoin

from aiohttp import ClientError, ClientResponseError, ClientSession


REST_MODE_VALUES = {
    "auto": "Automatic",
    "cool": "Cooling",
    "dry": "Dehumidifying",
    "fan": "Ventilating",
    "heat": "Heating",
    "off": "PowerOff",
}

MODE_ALIASES = {
    "automatic": "auto",
    "cooling": "cool",
    "dehumidifying": "dry",
    "ventilating": "fan",
    "heating": "heat",
    "poweroff": "off",
    "power_off": "off",
}

FAN_SPEED_VALUES = {
    "auto": "Auto",
    "speed1": "Speed1",
    "speed2": "Speed2",
    "speed3": "Speed3",
    "speed4": "Speed4",
    "speed5": "Speed5",
    "1": "Speed1",
    "2": "Speed2",
    "3": "Speed3",
    "4": "Speed4",
    "5": "Speed5",
}

SWING_VALUES = {
    "off": "Off",
    "pos1": "Pos1",
    "pos2": "Pos2",
    "pos3": "Pos3",
    "pos4": "Pos4",
    "pos5": "Pos5",
    "pos6": "Pos6",
    "1": "Pos1",
    "2": "Pos2",
    "3": "Pos3",
    "4": "Pos4",
    "5": "Pos5",
    "6": "Pos6",
}


class VestelAcError(Exception):
    """Base Vestel AC error."""


class VestelAcAuthError(VestelAcError):
    """Raised when authentication fails."""


class VestelAcApiError(VestelAcError):
    """Raised when Vestel API returns an error."""


@dataclass(frozen=True)
class VestelAcConfig:
    """Vestel AC configuration."""

    email: str
    password: str
    region: str
    user_pool_id: str
    app_client_id: str
    app_client_secret: str
    rest_base_url: str
    thing_name: str
    home_id: str
    product_line: str
    device_kind: str
    command_topic: str

    @property
    def resolved_command_topic(self) -> str:
        """Return configured or derived command topic."""
        if self.command_topic:
            return self.command_topic
        if self.home_id and self.product_line and self.device_kind and self.thing_name:
            return f"Vestel/{self.home_id}/{self.product_line}/{self.device_kind}/{self.thing_name}/toJson"
        return ""


def _secret_hash(username: str, client_id: str, client_secret: str) -> str:
    digest = hmac.new(
        client_secret.encode("utf-8"),
        msg=(username + client_id).encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def _extract_named_value(items: Any, name: str) -> Any:
    if isinstance(items, dict):
        return items.get(name)
    if isinstance(items, list):
        wanted = name.lower()
        for item in items:
            if not isinstance(item, dict):
                continue
            if str(item.get("item") or item.get("name") or "").lower() == wanted:
                return item.get("value")
    return None


def _first_not_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _normalize_bool_flag(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes", "on")


def _normalize_mode_key(value: Any) -> str | None:
    key = str(value or "").strip().lower()
    return MODE_ALIASES.get(key, key) or None


def normalize_fan_speed(value: Any) -> str | None:
    key = str(value or "").strip().lower()
    if not key:
        return None
    if key.startswith("climate.airconditioner.setting.fan.speed."):
        key = key.rsplit(".", 1)[-1].lower()
    if key not in FAN_SPEED_VALUES:
        raise ValueError(f"Invalid AC fan speed: {value}")
    return FAN_SPEED_VALUES[key]


def normalize_swing(value: Any, label: str) -> str | None:
    key = str(value or "").strip().lower()
    if not key:
        return None
    if key.startswith("climate.airconditioner.setting.fan."):
        key = key.rsplit(".", 1)[-1].lower()
    if key not in SWING_VALUES:
        raise ValueError(f"Invalid AC {label}: {value}")
    return SWING_VALUES[key]


def build_rest_properties(
    mode: str | None = None,
    temperature: float | int | None = None,
    fan_speed: str | None = None,
    vertical_swing: str | None = None,
    horizontal_swing: str | None = None,
    turbo: bool | None = None,
    eco: bool | None = None,
    sleep: bool | None = None,
) -> dict[str, Any]:
    """Build Vestel REST command properties."""
    commands: list[dict[str, Any]] = []
    settings: list[dict[str, Any]] = []
    mode_key = str(mode or "").strip().lower()
    mode_key = MODE_ALIASES.get(mode_key, mode_key)
    if mode_key:
        if mode_key not in REST_MODE_VALUES:
            raise ValueError(f"Invalid AC mode: {mode}")
        if mode_key == "off":
            commands.append({"item": "Command", "value": "PowerOff"})
        else:
            settings.append({"item": "Mode", "value": REST_MODE_VALUES[mode_key]})
    if temperature is not None:
        settings.append({"item": "Temperature", "value": max(16, min(30, int(float(temperature))))})
    normalized_fan_speed = normalize_fan_speed(fan_speed)
    if normalized_fan_speed:
        settings.append({"item": "Fan.Speed", "value": normalized_fan_speed})
    normalized_vertical_swing = normalize_swing(vertical_swing, "vertical swing")
    if normalized_vertical_swing:
        settings.append({"item": "Fan.VerticalSwing", "value": normalized_vertical_swing})
    normalized_horizontal_swing = normalize_swing(horizontal_swing, "horizontal swing")
    if normalized_horizontal_swing:
        settings.append({"item": "Fan.HorizontalSwing", "value": normalized_horizontal_swing})
    if turbo is not None:
        settings.append({"item": "Fan.Turbo", "value": bool(turbo)})
    if eco is not None:
        settings.append({"item": "Fan.Eco", "value": bool(eco)})
    if sleep is not None:
        settings.append({"item": "Fan.SleepMode", "value": bool(sleep)})

    properties: dict[str, Any] = {}
    if settings:
        properties["settings"] = settings
    if commands:
        properties["commands"] = commands
    return properties


class VestelAcClient:
    """Vestel HomeVSmart cloud client."""

    def __init__(self, session: ClientSession, config: VestelAcConfig) -> None:
        self._session = session
        self.config = config
        self._id_token = ""
        self._expires_at = 0.0
        self._login_lock = asyncio.Lock()
        self._last_status: dict[str, Any] = {}

    async def async_login(self) -> str:
        """Login and return cached ID token."""
        now = time.time()
        if self._id_token and now < self._expires_at - 120:
            return self._id_token

        async with self._login_lock:
            now = time.time()
            if self._id_token and now < self._expires_at - 120:
                return self._id_token

            auth_params = {"USERNAME": self.config.email, "PASSWORD": self.config.password}
            if self.config.app_client_secret:
                auth_params["SECRET_HASH"] = _secret_hash(
                    self.config.email,
                    self.config.app_client_id,
                    self.config.app_client_secret,
                )
            payload = {
                "AuthFlow": "USER_PASSWORD_AUTH",
                "ClientId": self.config.app_client_id,
                "AuthParameters": auth_params,
            }
            endpoint = f"https://cognito-idp.{self.config.region}.amazonaws.com/"
            try:
                async with self._session.post(
                    endpoint,
                    json=payload,
                    headers={
                        "Content-Type": "application/x-amz-json-1.1",
                        "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
                    },
                    timeout=20,
                ) as response:
                    data = await response.json(content_type=None)
                    if response.status >= 400:
                        raise VestelAcAuthError(str(data))
            except (ClientError, TimeoutError) as err:
                raise VestelAcAuthError(str(err)) from err

            result = data.get("AuthenticationResult") or {}
            id_token = str(result.get("IdToken") or "")
            if not id_token:
                raise VestelAcAuthError("Vestel Cognito login did not return an ID token")
            self._id_token = id_token
            self._expires_at = now + float(result.get("ExpiresIn") or 3600)
            return id_token

    async def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        token = await self.async_login()
        headers = {"Token": token, "Accept": "application/json", "Accept-Charset": "utf-8"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        url = urljoin(self.config.rest_base_url, path.lstrip("/"))
        try:
            async with self._session.request(
                method,
                url,
                json=body,
                headers=headers,
                timeout=30,
            ) as response:
                text = await response.text()
                data = await response.json(content_type=None) if text else None
                if response.status >= 400:
                    raise VestelAcApiError(f"HTTP {response.status}: {data}")
                return data
        except ClientResponseError as err:
            raise VestelAcApiError(str(err)) from err
        except (ClientError, TimeoutError) as err:
            raise VestelAcApiError(str(err)) from err

    async def async_status(self) -> dict[str, Any]:
        """Fetch and normalize AC status."""
        body = await self._request("GET", f"v1.0/appliances/{self.config.thing_name}/status")
        status = self._extract_status(body)
        self._last_status = dict(status)
        return status

    async def async_command(
        self,
        mode: str | None = None,
        temperature: float | int | None = None,
        fan_speed: str | None = None,
        vertical_swing: str | None = None,
        horizontal_swing: str | None = None,
        turbo: bool | None = None,
        eco: bool | None = None,
        sleep: bool | None = None,
    ) -> None:
        """Send a command to the AC."""
        properties = build_rest_properties(
            mode=mode,
            temperature=temperature,
            fan_speed=fan_speed,
            vertical_swing=vertical_swing,
            horizontal_swing=horizontal_swing,
            turbo=turbo,
            eco=eco,
            sleep=sleep,
        )
        if not properties:
            raise VestelAcApiError("No AC command was provided")
        topic = self.config.resolved_command_topic
        if not topic:
            raise VestelAcApiError("Command topic is missing")
        await self._request(
            "POST",
            f"v1.0/appliances/{self.config.thing_name}/command",
            {"properties": properties, "topic": topic},
        )

    def _extract_status(self, body: Any) -> dict[str, Any]:
        body = body if isinstance(body, dict) else {}
        properties = body.get("properties") if isinstance(body.get("properties"), dict) else body
        settings = properties.get("settings") if isinstance(properties, dict) else None
        status = properties.get("status") if isinstance(properties, dict) else None

        configured_mode = _first_not_none(
            _extract_named_value(settings, "Mode"),
            _extract_named_value(status, "Mode"),
        )
        current_mode = _extract_named_value(status, "CurrentMode")
        configured_mode_key = _normalize_mode_key(configured_mode)
        current_mode_key = _normalize_mode_key(current_mode)
        previous_mode_key = _normalize_mode_key(self._last_status.get("mode"))
        mode_key = configured_mode_key
        if mode_key in (None, "off") and current_mode_key not in (None, "off"):
            mode_key = current_mode_key
        if mode_key in (None, "off") and previous_mode_key not in (None, "off"):
            mode_key = previous_mode_key
        power_state = "off" if current_mode_key == "off" or configured_mode_key == "off" else "on"

        fan_speed = _extract_named_value(settings, "Fan.Speed")
        vertical_swing = _extract_named_value(settings, "Fan.VerticalSwing")
        horizontal_swing = _extract_named_value(settings, "Fan.HorizontalSwing")
        if power_state == "off":
            fan_speed = _first_not_none(self._last_status.get("fan_speed"), fan_speed)
            vertical_swing = _first_not_none(self._last_status.get("vertical_swing"), vertical_swing)
            horizontal_swing = _first_not_none(self._last_status.get("horizontal_swing"), horizontal_swing)
        else:
            fan_speed = _first_not_none(fan_speed, self._last_status.get("fan_speed"))
            vertical_swing = _first_not_none(vertical_swing, self._last_status.get("vertical_swing"))
            horizontal_swing = _first_not_none(horizontal_swing, self._last_status.get("horizontal_swing"))

        wifi_rssi = _extract_named_value(status, "Wifi.SignalRSS")
        return {
            "mode": mode_key or None,
            "mode_label": configured_mode,
            "current_mode": current_mode,
            "power_state": power_state,
            "target_temperature": _first_not_none(
                _extract_named_value(settings, "Temperature"),
                _extract_named_value(status, "Temperature"),
            ),
            "room_temperature": _first_not_none(
                _extract_named_value(status, "RoomTemperature"),
                _extract_named_value(settings, "RoomTemperature"),
            ),
            "fan_speed": normalize_fan_speed(fan_speed) if fan_speed is not None else None,
            "vertical_swing": normalize_swing(vertical_swing, "vertical swing") if vertical_swing is not None else None,
            "horizontal_swing": normalize_swing(horizontal_swing, "horizontal swing") if horizontal_swing is not None else None,
            "turbo": _normalize_bool_flag(_extract_named_value(settings, "Fan.Turbo")),
            "eco": _normalize_bool_flag(_extract_named_value(settings, "Fan.Eco")),
            "sleep": _normalize_bool_flag(_extract_named_value(settings, "Fan.SleepMode")),
            "wifi_rssi": int(wifi_rssi) if wifi_rssi is not None else None,
            "raw": body,
        }
