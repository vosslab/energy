# File structure

## Top-level layout
- [../AGENTS.md](../AGENTS.md): Local contribution and automation rules.
- [../README.md](../README.md): Repo overview, quick start, and documentation links.
- [../apps/](../apps/): Operational scripts that control devices using pricing data.
- [../awtrix3/](../awtrix3/): AWTRIX 3 tile scripts, configs, and authoring docs.
- [../battery_arbitrage/](../battery_arbitrage/): BLE battery reader and arbitrage scaffolding.
- [../devel/](../devel/): Developer helpers (for example, changelog tooling).
- [../docs/](../docs/): Repository documentation.
- [../energylib/](../energylib/): Shared Python modules for pricing, device APIs, and helpers.
- [../html/](../html/): CGI scripts for local dashboards.
- [../legacy/](../legacy/): Historical scripts retained for reference.
- [../plots/](../plots/): Pricing plot utilities.
- [../tests/](../tests/): Lint and ASCII compliance helpers.
- [../Brewfile](../Brewfile): Homebrew dependency manifest.
- [../pip_requirements.txt](../pip_requirements.txt): Python dependency manifest.
- [../run_all_screens.sh](../run_all_screens.sh): Screen-based launcher for recurring jobs.
- [../read_wemo_log.sh](../read_wemo_log.sh): Utility for reading WeMo logs.
- [../LICENSE](../LICENSE): Project license text.

## Key subtrees
- [../apps/](../apps/): ComEd pricing checks, Ecobee control, and WeMo control scripts.
- [../awtrix3/](../awtrix3/): Tile generators such as
  [../awtrix3/display_date.py](../awtrix3/display_date.py), sender
  [../awtrix3/send_price.py](../awtrix3/send_price.py), and YAML configs
  [../awtrix3/api.yml](../awtrix3/api.yml),
  [../awtrix3/sports_teams.yaml](../awtrix3/sports_teams.yaml), and
  [../awtrix3/garmin_login.yml](../awtrix3/garmin_login.yml).
- [../battery_arbitrage/](../battery_arbitrage/): BLE reader
  [../battery_arbitrage/battery_info.py](../battery_arbitrage/battery_info.py) and
  arbitrage entry point
  [../battery_arbitrage/main_arbitrage.py](../battery_arbitrage/main_arbitrage.py).
- [../energylib/](../energylib/): Core modules
  [../energylib/comedlib.py](../energylib/comedlib.py),
  [../energylib/ecobeelib.py](../energylib/ecobeelib.py), and
  [../energylib/commonlib.py](../energylib/commonlib.py).
- [../html/](../html/): CGI pages for ComEd pricing, solar, and usage.
- [../legacy/](../legacy/): Archived scripts and the
  [../legacy/lib_oled96/](../legacy/lib_oled96/) snapshot.

## Generated artifacts
- [../.gitignore](../.gitignore) excludes logs, CSV outputs, YAML configs, and temporary
  artifacts such as [../ascii_compliance.txt](../ascii_compliance.txt) and
  [../pyflakes.txt](../pyflakes.txt).
- Runtime outputs such as `*.csv` logs and cache files are expected to be generated
  outside the repo or ignored by git.

## Documentation map
- [INSTALL.md](INSTALL.md): Dependency manifests and requirements.
- [USAGE.md](USAGE.md): Entry points and configuration file locations.
- [FILES.md](FILES.md): Per-file guide to repo contents.
- [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md): Component overview and data flow.
- [FILE_STRUCTURE.md](FILE_STRUCTURE.md): Directory map and conventions.
- [wemoPlug-comed-multi.md](wemoPlug-comed-multi.md): WeMo decision logic notes.

## Where to add new work
- New shared Python logic: [../energylib/](../energylib/).
- New device automation scripts: [../apps/](../apps/).
- New AWTRIX tiles or integrations: [../awtrix3/](../awtrix3/).
- New dashboards: [../html/](../html/) or [../plots/](../plots/).
- New documentation: [../docs/](../docs/) using ALL CAPS filenames.
- New tests or lint helpers: [../tests/](../tests/).
