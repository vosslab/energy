# Energy automation scripts

This repo contains scripts and shared libraries for home energy automation, including
ComEd pricing, Ecobee thermostat control, WeMo plug control, AWTRIX display tiles, solar
production tracking, battery arbitrage, and CGI dashboards for a self-hosted setup where
you manage device credentials and local network access.

## Documentation

### Getting started
- [docs/INSTALL.md](docs/INSTALL.md) (`docs/INSTALL.md`): Dependencies and setup steps.
- [docs/USAGE.md](docs/USAGE.md) (`docs/USAGE.md`): Entry points, configuration, and runtime notes.

### Repo guides
- [docs/FILES.md](docs/FILES.md) (`docs/FILES.md`): Index of repo files and docs.
- [docs/FILE_STRUCTURE.md](docs/FILE_STRUCTURE.md) (`docs/FILE_STRUCTURE.md`): Directory map and placement conventions.
- [docs/CODE_ARCHITECTURE.md](docs/CODE_ARCHITECTURE.md) (`docs/CODE_ARCHITECTURE.md`): Component overview and data flow.
- [docs/CHANGELOG.md](docs/CHANGELOG.md) (`docs/CHANGELOG.md`): Chronological record of user-facing changes.

### Device notes
- [docs/wemoPlug-comed-multi.md](docs/wemoPlug-comed-multi.md) (`docs/wemoPlug-comed-multi.md`): Decision flow for the multi-plug controller.

## Quick start
- Follow [docs/INSTALL.md](docs/INSTALL.md) to install dependencies.
- From the repo root, run `python3 apps/checkPrices-comed.py` to print the last three
  ComEd prices and open a plot window.

For device credentials and YAML configuration files, see [docs/USAGE.md](docs/USAGE.md).
