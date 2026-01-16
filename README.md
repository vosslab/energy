# Energy automation scripts

This repo contains scripts and shared libraries for home energy automation, including ComEd
pricing, Ecobee thermostat control, WeMo plug control, AWTRIX display tiles, solar
production tracking, battery arbitrage, and CGI dashboards. It is intended for a
self-hosted setup where you manage device credentials and local network access.

## Documentation
- Install and dependencies: [docs/INSTALL.md](docs/INSTALL.md)
- Usage and entry points: [docs/USAGE.md](docs/USAGE.md)
- File guide: [docs/FILES.md](docs/FILES.md)
- WeMo multi-plug decision flow: [docs/wemoPlug-comed-multi.md](docs/wemoPlug-comed-multi.md)

## Quick start
- Follow [docs/INSTALL.md](docs/INSTALL.md) to install dependencies.
- From the repo root, run `python3 apps/checkPrices-comed.py` to print recent ComEd prices
  and open a plot window.

For device credentials and YAML configuration files, see [docs/USAGE.md](docs/USAGE.md).
