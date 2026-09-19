"""Constants for Vestel AC Custom."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "vestel_ac_custom"
PLATFORMS = ["climate"]

CONF_REST_BASE_URL = "rest_base_url"
CONF_THING_NAME = "thing_name"
CONF_HOME_ID = "home_id"
CONF_PRODUCT_LINE = "product_line"
CONF_DEVICE_KIND = "device_kind"
CONF_COMMAND_TOPIC = "command_topic"
CONF_REGION = "region"
CONF_USER_POOL_ID = "user_pool_id"
CONF_APP_CLIENT_ID = "app_client_id"
CONF_APP_CLIENT_SECRET = "app_client_secret"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_REST_BASE_URL = "https://sh-native-api.homevsmart.com/"
DEFAULT_REGION = "eu-west-1"
DEFAULT_USER_POOL_ID = "eu-west-1_EgDdXOayO"
DEFAULT_APP_CLIENT_ID = "6tl8koi5fis9j7i3u3jnv15vr7"
DEFAULT_PRODUCT_LINE = "HM07"
DEFAULT_DEVICE_KIND = "AC"
DEFAULT_SCAN_INTERVAL = 15

DEFAULT_UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

SERVICE_SET_TURBO = "set_turbo"
SERVICE_SET_ECO = "set_eco"
SERVICE_SET_SLEEP = "set_sleep"
