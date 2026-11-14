# File structure

## Top-level layout

- [../AGENTS.md](../AGENTS.md): Local contribution and automation rules.
- [../README.md](../README.md): Repo overview, quick start, and documentation links.
- [../apps/](../apps/): Operational scripts that control devices using pricing data.
- [../awtrix3/](../awtrix3/): AWTRIX 3 tile scripts, configs, and authoring docs.
- [../devel/](../devel/): Developer helpers (for example, changelog tooling).
- [docs/](.): Repository documentation.
- [../energylib/](../energylib/): Shared Python modules for pricing, device APIs, and helpers.
- [../html/](../html/): Static dashboard sources, TypeScript build config, and older CGI pages.
- [../legacy/](../legacy/): Historical scripts retained for reference.
- [../plots/](../plots/): Pricing plot utilities.
- [../scripts/](../scripts/): Dashboard data generation, build, and deploy scripts.
- [../tests/](../tests/): Behavioral tests, repository hygiene gates, and test helpers.
- [../tools/](../tools/): Standalone-utility location; currently contains its placement guide.
- [../Brewfile](../Brewfile): Homebrew dependency manifest.
- [../pip_requirements.txt](../pip_requirements.txt): Python dependency manifest.
- [../pip_requirements-dev.txt](../pip_requirements-dev.txt): Test and maintenance dependencies.
- [../package.json](../package.json): TypeScript dependency for the dashboard.
- [../VERSION](../VERSION): Repository version.
- [../source_me.sh](../source_me.sh): Sourced shell environment and Python runtime flags.
- [../run_all_tmux.sh](../run_all_tmux.sh): Tmux launcher for dashboard, WeMo, and display jobs.
- [../run_all_screens.sh](../run_all_screens.sh): Screen-based launcher for recurring jobs.
- [../read_wemo_log.sh](../read_wemo_log.sh): Utility for reading WeMo logs.
- [../LICENSE.GPL-3.0](../LICENSE.GPL-3.0): Project license text.

## Key subtrees

- [../apps/](../apps/): ComEd pricing checks, Ecobee control, and WeMo control scripts.
- [../awtrix3/](../awtrix3/): Tile generators such as
  [../awtrix3/display_date.py](../awtrix3/display_date.py), sender
  [../awtrix3/send_price.py](../awtrix3/send_price.py), and YAML configs
  `awtrix3/api.yml`,
  [../awtrix3/sports_teams.yaml](../awtrix3/sports_teams.yaml), and
  `awtrix3/garmin_login.yml`.
- Sports code is split between
  [../awtrix3/sports_schedule_sources.py](../awtrix3/sports_schedule_sources.py) for configuration
  and event fetching, and [../awtrix3/sports_schedule.py](../awtrix3/sports_schedule.py) for
  AWTRIX layout and delivery.
- [../energylib/](../energylib/): Core modules
  [../energylib/comedlib.py](../energylib/comedlib.py),
  [../energylib/ecobeelib.py](../energylib/ecobeelib.py), and
  [../energylib/commonlib.py](../energylib/commonlib.py).
- [../html/dashboard.html](../html/dashboard.html) and
  [../html/dashboard.ts](../html/dashboard.ts): Static dashboard frontend;
  [../html/tsconfig.json](../html/tsconfig.json) controls compilation. Other Python files in
  [../html/](../html/) provide older HTML/CGI views and static-page generation.
- [../scripts/generate_dashboard_data.py](../scripts/generate_dashboard_data.py) writes live
  dashboard JSON and ComEd HTML;
  [../scripts/build_dashboard.sh](../scripts/build_dashboard.sh) builds the frontend;
  [../scripts/deploy_dashboard.sh](../scripts/deploy_dashboard.sh) copies static assets.
- [../tests/file_utils.py](../tests/file_utils.py) supports repository-wide discovery and
  reports; [../tests/conftest.py](../tests/conftest.py) supplies test configuration.
- [../devel/DEVEL_README.md](../devel/DEVEL_README.md) describes the maintenance folder, including
  version, changelog, release, and repository-mapping helpers.
- [../legacy/](../legacy/): Archived scripts and the
  [../legacy/lib_oled96/](../legacy/lib_oled96/) snapshot.

## Generated artifacts

- [../.gitignore](../.gitignore) excludes `report_*.txt`, CSV outputs, local `.yml` configuration,
  `pyecobee_db*`, root `output*` directories, Graphify output, and temporary test work.
- Dashboard JavaScript is generated under `html/build/`; that directory and
  `html/dashboard.js` are ignored. Deployment copies the compiled file to the web root.
- Runtime dashboard data defaults to `/var/www/html/api/`; the generator also writes
  `/var/www/html/comed.html`. These outputs are outside the source tree.
- The ComEd JSON cache uses `/tmp/comed_cache_file.json`; Ecobee credentials use
  `/etc/energy/pyecobee_db.pickle`. These runtime files are outside the source tree.
- [../run_all_tmux.sh](../run_all_tmux.sh) and
  [../run_all_screens.sh](../run_all_screens.sh) append job output to `/dev/shm/<session>.log`.

## Documentation map

- [INSTALL.md](INSTALL.md): Dependency manifests and requirements.
- [USAGE.md](USAGE.md): Entry points and configuration file locations.
- [FILES.md](FILES.md): Per-file guide to repo contents.
- [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md): Component overview and data flow.
- [FILE_STRUCTURE.md](FILE_STRUCTURE.md): Directory map and conventions.
- [CHANGELOG.md](CHANGELOG.md): User-facing changes and implementation notes.
- [REPO_STYLE.md](REPO_STYLE.md): File placement and repository conventions.
- [PYTEST_STYLE.md](PYTEST_STYLE.md): Test policy and test lanes.
- [../awtrix3/AWTRIX3_AUTHORING_GUIDE.md](../awtrix3/AWTRIX3_AUTHORING_GUIDE.md): Display authoring
  and layout guidance.
- [wemoPlug-comed-multi.md](wemoPlug-comed-multi.md): WeMo decision logic notes.

## Where to add new work

- New shared Python logic: [../energylib/](../energylib/).
- New device automation scripts: [../apps/](../apps/).
- New AWTRIX tiles or integrations: [../awtrix3/](../awtrix3/).
- New dashboards: [../html/](../html/), [../plots/](../plots/), or [../scripts/](../scripts/).
- New documentation: [docs/](.) using ALL CAPS filenames.
- New tests or lint helpers: [../tests/](../tests/).
- Maintainer commands: [../devel/](../devel/); optional standalone utilities: [../tools/](../tools/).
- Generated artifacts: root `output/` or a purpose-specific root `output_<purpose>/` directory,
  following [REPO_STYLE.md](REPO_STYLE.md).
