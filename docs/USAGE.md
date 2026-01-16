# Usage

Scripts are grouped by area under `apps/`, `awtrix3/`, `battery_arbitrage/`, `html/`, and
`legacy/`, with shared modules in `energylib/`. Many scripts need local network access or
device credentials. See [docs/FILES.md](FILES.md) for the full directory map.

## Entry points
- `apps/checkPrices-comed.py` prints recent ComEd prices and shows a plot.
- `apps/thermostat-comed.py` adjusts Ecobee cooling based on ComEd pricing.
- `apps/wemoPlug-comed-multi.py` controls WeMo plugs using ComEd pricing.
- `awtrix3/send_price.py` sends ComEd, solar, date, and sports tiles to AWTRIX 3.
- `battery_arbitrage/main_arbitrage.py` prints pricing data used for arbitrage decisions.

## Configuration files
- `awtrix3/api.yml` stores AWTRIX credentials for `awtrix3/` scripts.
- `awtrix3/sports_teams.yaml` configures tracked teams for `awtrix3/sports_schedule.py`.
- `awtrix3/garmin_login.yml` stores Garmin credentials for `awtrix3/display_garmin_connect.py`.
- `ecobee_defs.yml` is loaded from `/etc/energy/ecobee_defs.yml` or the current directory by
  `energylib/ecobeelib.py`.
- `arbitrage_config.yml` is loaded from the current working directory by
  `battery_arbitrage/battery_info.py`.

## Automation helper
- `run_all_screens.sh` launches long-running jobs in `screen` and uses hard-coded
  `/home/pi/energy` paths. Update the paths before running on other hosts.
