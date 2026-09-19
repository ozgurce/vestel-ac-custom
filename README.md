# Vestel AC Custom

Home Assistant custom integration for Vestel / HomeVSmart air conditioners.

This integration was built from a working local Vestel AC control implementation. It uses Vestel's Cognito login and native API to expose the air conditioner as a Home Assistant climate entity.

## Features

- Power on/off
- HVAC modes: heat, cool, auto, dry, fan only
- Target temperature, 16-30 C
- Room temperature
- Fan speed: Auto, Speed1-Speed5
- Vertical swing positions: Off, Pos1-Pos6
- Horizontal swing positions: Auto, Pos1-Pos5
- Immediate optimistic state updates after successful commands, followed by short cloud refreshes
- Faster status polling, capped at 15 seconds so external changes appear sooner
- Extra services for Turbo, Eco, and Sleep mode

## HACS installation

1. Open HACS in Home Assistant.
2. Add `https://github.com/ozgurce/vestel-ac-custom` as a custom repository with type `Integration`.
3. Install `Vestel AC Custom`.
4. Restart Home Assistant.
5. Add the integration from **Settings > Devices & services > Add integration**.

## Required setup values

The integration needs your Vestel / HomeVSmart account and the appliance identifiers for your own air conditioner:

- Email
- Password
- Thing name
- Home ID
- Product line, usually `HM07`
- Device kind, usually `AC`

Advanced defaults are included for the currently known Vestel HomeVSmart API:

- REST base URL: `https://sh-native-api.homevsmart.com/`
- Region: `eu-west-1`
- User pool ID: `eu-west-1_EgDdXOayO`
- App client ID: `6tl8koi5fis9j7i3u3jnv15vr7`

If Vestel changes the mobile app backend, these can be adjusted from the integration setup form.

## How to find the setup values

Only use values from your own Vestel / HomeVSmart account and your own air conditioner. Do not publish your email, password, client secret, tokens, or full raw API captures.

### Option 1: Migrating from an existing local controller

If you already have a working local controller or script, copy the values from its Vestel AC configuration.

For example, in the original PC control project these values were stored in a settings file similar to:

```json
{
  "vestel_ac": {
    "email": "your-account@example.com",
    "password": "your-password",
    "rest_base_url": "https://sh-native-api.homevsmart.com/",
    "thing_name": "WG_AC_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "home_id": "1234567",
    "product_line": "HM07",
    "device_kind": "AC",
    "command_topic": "Vestel/1234567/HM07/AC/WG_AC_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/toJson"
  }
}
```

The command topic can usually be built from the other identifiers:

```text
Vestel/<home_id>/<product_line>/<device_kind>/<thing_name>/toJson
```

For most Vestel air conditioners:

- Product line: `HM07`
- Device kind: `AC`
- REST base URL: `https://sh-native-api.homevsmart.com/`
- Region: `eu-west-1`
- User pool ID: `eu-west-1_EgDdXOayO`
- App client ID: `6tl8koi5fis9j7i3u3jnv15vr7`

### Option 2: Reading the values from your own HomeVSmart app traffic

If you do not already have the identifiers, you can inspect the network traffic from the official Vestel / HomeVSmart mobile app while logged in with your own account.

A typical workflow is:

1. Install a local HTTPS inspection tool such as HTTP Toolkit, Proxyman, Charles Proxy, or mitmproxy on your computer.
2. Configure your phone to use that tool as its Wi-Fi proxy.
3. Install the tool's local certificate on your phone so HTTPS requests from your own phone can be inspected.
4. Open the official Vestel / HomeVSmart app, log in, and open or control your air conditioner.
5. Search the captured requests for paths like:
   - `/v1.0/appliances`
   - `/v1.0/appliances/<thing_name>/status`
   - `/v1.0/appliances/<thing_name>/command`
6. Copy these values from the requests and JSON responses:
   - `thing_name`: often looks like `WG_AC_...`
   - `home_id`: the numeric home identifier
   - `product_line`: usually `HM07`
   - `device_kind`: usually `AC`
   - `command_topic`: often sent with command requests
   - `rest_base_url`: usually `https://sh-native-api.homevsmart.com/`

During login you may also see a Cognito request to an AWS endpoint. If the default login settings stop working in the future, the current `region`, `app_client_id`, and possibly `app_client_secret` can be read from that login request. Most users should leave the advanced Cognito fields at their defaults unless login fails.

### What each field means

| Field | Where it comes from | Example |
| --- | --- | --- |
| Email | Your Vestel / HomeVSmart account | `your-account@example.com` |
| Password | Your Vestel / HomeVSmart account | Do not share |
| Thing name | Appliance API identifier | `WG_AC_...` |
| Home ID | Home identifier in the Vestel API | `1234567` |
| Product line | Appliance product line | `HM07` |
| Device kind | Appliance type | `AC` |
| Command topic | MQTT-like command topic used by Vestel's API | `Vestel/<home_id>/HM07/AC/<thing_name>/toJson` |
| REST base URL | Vestel API base URL | `https://sh-native-api.homevsmart.com/` |
| Region | Cognito AWS region | `eu-west-1` |
| User pool ID | Cognito user pool | `eu-west-1_EgDdXOayO` |
| App client ID | Cognito app client | `6tl8koi5fis9j7i3u3jnv15vr7` |
| App client secret | Cognito app client secret, if required | Do not share |

If setup fails with `Vestel login failed`, first verify the email and password in the official app. If setup fails with `Could not connect to Vestel`, verify the `thing_name`, `home_id`, `command_topic`, and REST base URL.

## Services

After installation, these service actions are available:

- `vestel_ac_custom.set_turbo`
- `vestel_ac_custom.set_eco`
- `vestel_ac_custom.set_sleep`

Each service takes:

- `entity_id`
- `enabled`

## Notes

This is an unofficial integration and is not affiliated with Vestel.

## Publishing to the HACS default store

This repository is prepared for HACS validation with GitHub Actions. Before submitting it to HACS defaults:

1. Make sure the HACS and Hassfest GitHub Actions pass.
2. Create a full GitHub release, for example `v0.1.0`.
3. Fork `hacs/default`.
4. Add the repository to the `integration` list alphabetically.
5. Open a pull request from your personal fork.
