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
- Horizontal swing positions: Off, Pos1-Pos6
- Extra services for Turbo, Eco, and Sleep mode

## HACS installation

1. Open HACS in Home Assistant.
2. Add `https://github.com/ozgurce/vestel-ac-custom` as a custom repository with type `Integration`.
3. Install `Vestel AC Custom`.
4. Restart Home Assistant.
5. Add the integration from **Settings > Devices & services > Add integration**.

## Required setup values

The first version expects the known Vestel appliance identifiers:

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
