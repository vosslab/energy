# Code architecture

## Overview

This repo is a collection of Python scripts and shared modules for home energy
automation. The core workflows fetch ComEd pricing data, derive decisions, and
control devices such as Ecobee thermostats, WeMo plugs, and AWTRIX 3 displays.
Supporting scripts generate a static TypeScript dashboard, HTML pages, and CGI plots.
Python dependencies live in [../pip_requirements.txt](../pip_requirements.txt);
[../package.json](../package.json) declares TypeScript for the dashboard build.

## Major components

- [../energylib/comedlib.py](../energylib/comedlib.py) downloads and caches ComEd prices,
  computes current/predicted rates and cutoffs, and owns freshness checks. It uses Requests,
  NumPy, and SciPy.
- [../energylib/ecobeelib.py](../energylib/ecobeelib.py) wraps pyecobee for thermostat
  authorization, sensors, runtime data, and holds. Existing credential pickles load through
  a restricted class lookup. [../energylib/solarProduction.py](../energylib/solarProduction.py)
  reads the local inverter and uses PyEphem to determine daylight.
- [../apps/](../apps/) contains price-driven WeMo and Ecobee controllers and manual
  thermostat commands. The WeMo controller uses pywemo's discovery and switching API.
- [../awtrix3/](../awtrix3/) builds display payloads and posts them to AWTRIX HTTP endpoints.
  [../awtrix3/sports_schedule_sources.py](../awtrix3/sports_schedule_sources.py) owns sports
  configuration and ESPN/Ergast fetching;
  [../awtrix3/sports_schedule.py](../awtrix3/sports_schedule.py) owns layout, CLI, and delivery.
- [../scripts/](../scripts/) generates dashboard data and builds/deploys the static frontend.
  [../html/](../html/) contains the TypeScript/HTML frontend and older CGI pages;
  [../plots/plot_comed.py](../plots/plot_comed.py) renders a Matplotlib price plot.
- [../run_all_tmux.sh](../run_all_tmux.sh) and
  [../run_all_screens.sh](../run_all_screens.sh) launch recurring jobs. Tests and maintenance
  commands live in [../tests/](../tests/) and [../devel/](../devel/).
- [../legacy/](../legacy/) retains earlier controllers, usage readers, and an OLED driver.

## Data flow

### Pricing and device control

1. [../energylib/comedlib.py](../energylib/comedlib.py) downloads the ComEd five-minute feed
   through an in-memory/persistent JSON cache and derives rates and cutoffs.
2. [../apps/wemoPlug-comed-multi.py](../apps/wemoPlug-comed-multi.py) checks freshness and
   chooses enable, disable, or hold for each configured plug. Failed discovery reports an
   unavailable plug and retries on the next control action.
3. [../apps/thermostat-comed.py](../apps/thermostat-comed.py) reads pricing and thermostat
   conditions, then applies cooling adjustments through the Ecobee wrapper.

`isPriceDataFresh` and `STALE_PRICE_SECONDS` in
[../energylib/comedlib.py](../energylib/comedlib.py) define price freshness. Stale data makes
the WeMo controller request off and the thermostat controller assume a conservative high
price. An unreachable device cannot confirm that a requested action took effect.

### Dashboard generation and serving

1. [../scripts/generate_dashboard_data.py](../scripts/generate_dashboard_data.py) independently
   fetches ComEd, Ecobee, and solar data. JSON files are written atomically to the configured
   output directory, which defaults to `/var/www/html/api`.
2. The generator also writes `/var/www/html/comed.html` using
   [../energylib/htmltools.py](../energylib/htmltools.py). Its HTML output path is fixed even
   when the JSON output directory changes.
3. [../scripts/build_dashboard.sh](../scripts/build_dashboard.sh) compiles
   [../html/dashboard.ts](../html/dashboard.ts) under
   [../html/tsconfig.json](../html/tsconfig.json) to `html/build/dashboard.js`.
4. [../scripts/deploy_dashboard.sh](../scripts/deploy_dashboard.sh) copies the compiled script
   and [../html/dashboard.html](../html/dashboard.html) to `/var/www/html`.
5. The browser fetches `api/comed.json`, `api/ecobee.json`, and `api/solar.json` independently;
   Chart.js is loaded from a CDN. Stale ComEd payloads have `stale: true` and null current and
   predicted rates, which render as unknown.

[../run_all_tmux.sh](../run_all_tmux.sh) repeats the JSON/static-HTML generator, while
[../run_all_screens.sh](../run_all_screens.sh) repeats the older
[../html/generate_comed_html.py](../html/generate_comed_html.py) HTML generator.

### AWTRIX displays

[../awtrix3/send_price.py](../awtrix3/send_price.py) gathers solar, price, and date payloads,
then posts them using credentials from local `awtrix3/api.yml`. Sports sending is commented
out in this sender. The sports CLI can separately load enabled entries from
[../awtrix3/sports_teams.yaml](../awtrix3/sports_teams.yaml), fetch events through
[../awtrix3/sports_schedule_sources.py](../awtrix3/sports_schedule_sources.py), and render or
send their payloads through [../awtrix3/sports_schedule.py](../awtrix3/sports_schedule.py).

## Testing and verification

- Run `source source_me.sh && python3 -m pytest tests/` for the fast suite. Dependencies are
  declared in [../pip_requirements-dev.txt](../pip_requirements-dev.txt).
- [../tests/test_comed_freshness.py](../tests/test_comed_freshness.py) covers stale-price
  behavior; [../tests/test_apps__wemoPlug_comed_multi.py](../tests/test_apps__wemoPlug_comed_multi.py)
  mocks discovery failures and recovery;
  [../tests/test_energylib__ecobeelib.py](../tests/test_energylib__ecobeelib.py) checks saved
  credentials and rejects unsupported pickle globals.
- Repository gates check Bandit findings, pyflakes, imports, shebangs/executable bits, source
  line limits, Markdown links, and formatting. Some hardware-dependent modules remain skipped.
- [../tests/file_utils.py](../tests/file_utils.py) provides tracked-file discovery and reports;
  [../tests/conftest.py](../tests/conftest.py) owns import setup and repository exclusions.

## Extension points

- Add shared logic in [../energylib/](../energylib/) for new APIs or data processing.
- Add new operational scripts in [../apps/](../apps/) for device control tasks.
- Add AWTRIX tiles in [../awtrix3/](../awtrix3/). Keep sports source adapters separate from
  display layout, and enable sports entries in
  [../awtrix3/sports_teams.yaml](../awtrix3/sports_teams.yaml).
- Add new dashboards or visualizations under [../html/](../html/), [../plots/](../plots/), and
  [../scripts/](../scripts/).

## Known gaps

- Verify deployment paths: both launchers use `/home/vosslab/nsh/energy`, while several older
  HTML scripts still append `/home/pi/energy` to their import path.
- Verify how the web server invokes older HTML scripts that now have no shebang or executable
  bit; its Python handler/CGI configuration is outside this repository.
- Confirm live WeMo discovery, thermostat authorization, inverter access, and AWTRIX delivery
  on the deployment network; offline tests do not verify these services.
