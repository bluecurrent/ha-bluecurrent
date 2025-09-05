# Blue Current Home Assistant integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

The Blue Current integration allows you to connect to your blue current account to Home Assistant and monitor your charge point(s).

> **Please note:**
>
> This Blue Current HACS integration may include **new, unstable experimental beta features**, which are subject to change or removal in future updates.
>
> For a **stable version of the Blue Current integration**, install it directly from Home Assistant (more information can be found [here](https://www.home-assistant.io/integrations/blue_current/)).

## Prerequisites
1. Log in to [my.bluecurrent.nl](https://my.bluecurrent.nl/).
2. Click on your username and go to settings.
3. Enable advanced options.
4. Click on your username again and go to advanced.
5. Generate an API token.


## Installation

-  [HACS](https://hacs.xyz/): add url https://github.com/bluecurrent/ha-bluecurrent as custom repository (HACS > Integration > option: Custom Repositories)
- Restart Home Assistant.
- Add 'Blue current' integration via HA Settings > 'Devices and Services' > 'Integrations'.
- Provide your api key.

## Configuration is done in the UI

# Platforms

## Sensor
The Blue Current integration provides the following sensors:
### Charge point sensors
- Activity
- Average current
- Average voltage
- Energy usage in kWh
- Max usage in Amps
  - The max amps the charge point can use.
- Offline since
- Started on
- Stopped on
- Total cost in EUR
- Total kW (estimate)
- Vehicle status

The following sensors are created as well, but disabled by default:
- Current phase 1-3
- offline max usage
- remaining current
- smart charging max usage
- Voltage phase 1-3
### Grid sensors
- Grid average current
- Grid max current

The following sensors are created as well, but disabled by default:
- Grid current phase 1-3

## Switch
The Blue Current integration provides the following switches:

- Toggle Plug & Charge
  - Allows you to start a session without having to scan a card.
- Toggle linked charging cards only
  - When enabled, visitors can't make use of the charge point. Only linked charging cards are allowed.
- Toggle charge point block
  - Enables or disables a charge point.

## Button
The Blue Current integration provides the following buttons:

- Stop session
- Reset
- Reboot
- Boost charge session
  - A charge session can be boosted when smart charging is enabled.

## Actions
The following actions are provided by the Blue Current integration:

### Action start_charge_session

Starts a new charge session. When no charging card ID is provided, no charging card will be used.

| Data attribute | Optional | Description |
| -------------- | -------- | ----------- |
| `device_id` | no | Charge point device ID |
| `charging_card_id` | yes | Charging card ID that will be used to start a charge session. |
