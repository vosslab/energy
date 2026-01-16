# Code architecture

## Overview
This repo is a collection of Python scripts and shared modules for home energy
automation. The core workflows fetch ComEd pricing data, derive decisions, and
control devices such as Ecobee thermostats, WeMo plugs, and AWTRIX 3 displays.
Supporting scripts generate plots and CGI pages for local dashboards.

## Major components
- [../energylib/](../energylib/): Shared Python modules for pricing, device APIs, and helpers.
- [../apps/](../apps/): Operational scripts that read pricing data and control devices.
- [../awtrix3/](../awtrix3/): AWTRIX 3 tile generators and senders, plus YAML config.
- [../battery_arbitrage/](../battery_arbitrage/): BLE battery query utilities and arbitrage
  scaffolding.
- [../html/](../html/): CGI scripts for local web dashboards.
- [../plots/](../plots/): Plotting utilities for pricing visualization.
- [../legacy/](../legacy/): Historical scripts retained for reference.

## Data flow
- [../energylib/comedlib.py](../energylib/comedlib.py) fetches ComEd price data and computes
  derived metrics.
- App scripts in [../apps/](../apps/) call `comedlib` for pricing and apply decisions:
  - [../apps/wemoPlug-comed-multi.py](../apps/wemoPlug-comed-multi.py) enables or disables
    WeMo plugs.
  - [../apps/thermostat-comed.py](../apps/thermostat-comed.py) adjusts Ecobee cooling settings.
- AWTRIX scripts in [../awtrix3/](../awtrix3/) build payloads and send them via HTTP APIs.
- CGI scripts in [../html/](../html/) and plotting scripts in [../plots/](../plots/) visualize
  the same data.

## Testing and verification
- [../tests/run_pyflakes.sh](../tests/run_pyflakes.sh) runs pyflakes checks for Python code.
- [../tests/run_ascii_compliance.py](../tests/run_ascii_compliance.py) and
  [../tests/run_ascii_compliance.sh](../tests/run_ascii_compliance.sh) check ASCII compliance
  in repo files.

## Extension points
- Add shared logic in [../energylib/](../energylib/) for new APIs or data processing.
- Add new operational scripts in [../apps/](../apps/) for device control tasks.
- Add new AWTRIX tiles in [../awtrix3/](../awtrix3/) and register configs in
  [../awtrix3/sports_teams.yaml](../awtrix3/sports_teams.yaml) when needed.
- Add new dashboards or visualizations under [../html/](../html/) and [../plots/](../plots/).

## Known gaps
- Verify the intended deployment layout and host paths (for example,
  [../run_all_screens.sh](../run_all_screens.sh) uses `/home/pi/energy`).
- Confirm required YAML credentials and config file locations for each device.
