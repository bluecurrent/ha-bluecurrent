# Integration Blueprint

[![hacs][hacsbadge]][hacs]

**This integration will set up the following platforms.**

Platform | Description
-- | --
`sensor` | Show data from a charge point.
`switch` | Switch something `True` or `False`.
`button` | Run an action.

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `blue_current`.
1. Download _all_ the files from the `custom_components/blue_current/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Integration blueprint"

## Configuration is done in the UI

<!---->
***
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge