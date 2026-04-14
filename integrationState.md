# Current state Blue Current Home Assistant integration

The Blue Current integration allows users to connect their Blue Current account to Home Assistant and monitor their charge point(s).

## Integration

The Blue Current Home Assistant integration is split in two components:

- Home assistant code
- Blue Current Home Assistant API

The Home Assistant code part of the integration contains all code that enables the integration with Home Assistant, such as button and switch definitions.

To interact with the Blue Current backend, the HomeAssistantAPI library is used:  
https://github.com/bluecurrent/HomeAssistantAPI

This library enables the Home Assistant code to interact with the Blue Current WebSocket, which is used to communicate with the backend.

## Versions

Currently, two Blue Current Home Assistant integrations exist:

- [The 'Offical' integration (called the 'Core' integration in this document): This integration can be downloaded via the offical Home Assistant store.](https://github.com/bluecurrent/core/tree/dev/homeassistant/components/blue_current)
- [The HACS integration: This integration can only be downloaded when a user has HACS installed](https://github.com/bluecurrent/ha-bluecurrent)

Because the HACS integration does not require a code review from Home Assistant, we first test Home Assistant features in the HACS integration.
Once the feature is tested in the HACS integration and is considered stable, it can be implemenated in the Core integration.
Because we test functionality in the HACS integration first, this version most likely contains more functionality than the Core integration.

Features that require testing, are published on HACS as Pre-release (via GitHub releases).

_Current pre-release versions: [v0.3.0](https://github.com/bluecurrent/ha-bluecurrent/releases/tag/v0.3.0), [v0.4.0](https://github.com/bluecurrent/ha-bluecurrent/releases/tag/v0.4.0) and [v0.5.0](https://github.com/bluecurrent/ha-bluecurrent/releases/tag/v0.5.0)_

## Features in Core and HACS

- **Services**
  - Start charge session
    - Requires a device ID.
    - A charging card can be provided; defaults to no charging card when starting a charge session.
- **Buttons**
  - Reset chargepoint
  - Reboot chargepoint
  - Stop charging (when charging)
- **Switch**
  - Enable/disable Plug and Charge
  - Enable/disable Linked charging cards only
  - Enable/disable chargepoint block

## Extra features in HACS (not yet available in Core)

- **Services**
  - User override
    - Requires Device ID('s), Current, Override start / end days and Override start / end time.
  - Clear user override
    - Requires Device ID('s).
  - Set Price based charging
    - Requires Device ID.
    - Optional battery size and minimum percentage.
  - Update Price based charging
    - Requires Device ID.
    - Optional expected departure time and current battery percentage.
  - Set Delayed charging
  - Requires Device ID, Days, End time and Start time.

## Features in development

Currently, the get transactions feature is still in development. Get transactions is a service that let's a user retrieve their transactions via Home Assistant.

The current branch can be found here: https://github.com/bluecurrent/ha-bluecurrent/tree/get-transactions
