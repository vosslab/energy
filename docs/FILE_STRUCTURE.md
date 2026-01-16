# File structure

## Top-level layout
- `AGENTS.md`: Local contribution and automation rules.
- `README.md`: Repo overview, quick start, and documentation links.
- `apps/`: Operational scripts that control devices using pricing data.
- `awtrix3/`: AWTRIX 3 tile scripts, configs, and authoring docs.
- `battery_arbitrage/`: BLE battery reader and arbitrage scaffolding.
- `devel/`: Developer helpers (for example, changelog tooling).
- `docs/`: Repository documentation.
- `energylib/`: Shared Python modules for pricing, device APIs, and helpers.
- `html/`: CGI scripts for local dashboards.
- `legacy/`: Historical scripts retained for reference.
- `plots/`: Pricing plot utilities.
- `tests/`: Lint and ASCII compliance helpers.
- `Brewfile`: Homebrew dependency manifest.
- `pip_requirements.txt`: Python dependency manifest.
- `run_all_screens.sh`: Screen-based launcher for recurring jobs.
- `read_wemo_log.sh`: Utility for reading WeMo logs.
- `LICENSE`: Project license text.

## Key subtrees
- `apps/`: ComEd pricing checks, Ecobee control, and WeMo control scripts.
- `awtrix3/`: Tile generators (`*_display.py`), sender (`send_price.py`), and
  YAML configs (`api.yml`, `sports_teams.yaml`, `garmin_login.yml`).
- `battery_arbitrage/`: BLE reader (`battery_info.py`) and pricing-driven
  arbitrage entry point (`main_arbitrage.py`).
- `energylib/`: Core modules (`comedlib.py`, `ecobeelib.py`, `commonlib.py`).
- `html/`: CGI pages for ComEd pricing, solar, and usage.
- `legacy/`: Archived scripts and the `lib_oled96/` snapshot.

## Generated artifacts
- `.gitignore` excludes logs, CSV outputs, YAML configs, and temporary artifacts
  such as `ascii_compliance.txt` and `pyflakes.txt`.
- Runtime outputs such as `*.csv` logs and cache files are expected to be
  generated outside the repo or ignored by git.

## Documentation map
- `docs/INSTALL.md`: Dependency manifests and requirements.
- `docs/USAGE.md`: Entry points and configuration file locations.
- `docs/FILES.md`: Per-file guide to repo contents.
- `docs/CODE_ARCHITECTURE.md`: Component overview and data flow.
- `docs/FILE_STRUCTURE.md`: Directory map and conventions.
- `docs/wemoPlug-comed-multi.md`: WeMo decision logic notes.

## Where to add new work
- New shared Python logic: `energylib/`.
- New device automation scripts: `apps/`.
- New AWTRIX tiles or integrations: `awtrix3/`.
- New dashboards: `html/` or `plots/`.
- New documentation: `docs/` using ALL CAPS filenames.
- New tests or lint helpers: `tests/`.
