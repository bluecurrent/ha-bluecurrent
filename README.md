# Blue Current Home Assistant integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

The Blue Current integration allows you to connect to your blue current account to Home Assistant and monitor your charge point(s).


## Prerequisites
1. Log in to [my.bluecurrent](https://my.bluecurrent.nl/).
2. Goto settings and enable developer mode.
3. Generate an API token.


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

- Block
    - Enables or disables a charge point.
- Plug and charge
    - Allows you to start a session without having to scan a card.
- Linked charge cards only
    - Toggles if the chargepoint is usable with unlinked charge cards.

## Button
The Blue Current integration provides the following buttons:

- Start session
- Stop session
- Reset
- Reboot