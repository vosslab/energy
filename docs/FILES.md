# File guide

High-level purpose of each file and folder in this repo.

## Docs
- [../AGENTS.md](../AGENTS.md) describes local instructions for contributors.
- [../README.md](../README.md) summarizes the repo purpose and quick start.
- [CHANGELOG.md](CHANGELOG.md) tracks notable repo changes.
- [../LICENSE](../LICENSE) defines the project license.
- [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) summarizes components and data flow.
- [FILE_STRUCTURE.md](FILE_STRUCTURE.md) documents the repo layout and conventions.
- [INSTALL.md](INSTALL.md) lists dependency manifests and requirements.
- [MARKDOWN_STYLE.md](MARKDOWN_STYLE.md) defines documentation style rules.
- [PYTHON_STYLE.md](PYTHON_STYLE.md) defines Python coding style rules.
- [USAGE.md](USAGE.md) lists entry points and configuration files.
- [wemoPlug-comed-multi.md](wemoPlug-comed-multi.md) documents the multi-plug decision
  logic.

## Top-level scripts
- [../run_all_screens.sh](../run_all_screens.sh) launches recurring scripts in `screen`
  sessions.

## Apps directory
- [../apps/checkPrices-comed.py](../apps/checkPrices-comed.py) prints recent ComEd prices
  and plots the current day.
- [../apps/ecobeeEndOfHourOverride.py](../apps/ecobeeEndOfHourOverride.py) sets an Ecobee
  hold that ends at the hour.
- [../apps/setEcobeeTemp.py](../apps/setEcobeeTemp.py) sets an Ecobee hold to a specific
  end time.
- [../apps/thermostat-comed.py](../apps/thermostat-comed.py) adjusts Ecobee cooling based
  on ComEd prices and humidity.
- [../apps/wemoPlug-comed-old2.py](../apps/wemoPlug-comed-old2.py) WeMo controller using
  updated `pywemo` calls.
- [../apps/wemoPlug-comed-multi.py](../apps/wemoPlug-comed-multi.py) multi-plug WeMo
  controller using the old2 pricing logic.

## Energy library directory
- [../energylib/__init__.py](../energylib/__init__.py) marks the shared modules package.
- [../energylib/comedlib.py](../energylib/comedlib.py) fetches ComEd pricing data and
  computes derived rate metrics.
- [../energylib/commonlib.py](../energylib/commonlib.py) provides shared utilities
  (string cleanup, hashing, file helpers).
- [../energylib/ecobeelib.py](../energylib/ecobeelib.py) wraps Ecobee auth and thermostat
  data access via `pyecobee`.
- [../energylib/htmltools.py](../energylib/htmltools.py) renders HTML snippets for ComEd
  and Ecobee data.
- [../energylib/solarProduction.py](../energylib/solarProduction.py) queries the inverter
  API and checks daylight status.

## Plots directory
- [../plots/plot_comed.py](../plots/plot_comed.py) generates a ComEd pricing plot as a CGI
  image.

## Awtrix3 directory
- [../awtrix3/comed_price_display.py](../awtrix3/comed_price_display.py) builds AWTRIX
  payloads for ComEd price display.
- [../awtrix3/display_date.py](../awtrix3/display_date.py) builds an AWTRIX date tile with
  custom drawing.
- [../awtrix3/display_garmin_connect.py](../awtrix3/display_garmin_connect.py) reads Garmin
  Connect distances for display.
- [../awtrix3/icon_draw.py](../awtrix3/icon_draw.py) defines AWTRIX icon IDs and arrow draw
  helpers.
- [../awtrix3/send_price.py](../awtrix3/send_price.py) posts solar, price, and date tiles
  to an AWTRIX 3.
- [../awtrix3/solar_display.py](../awtrix3/solar_display.py) builds AWTRIX payloads for
  solar production.
- [../awtrix3/sun_location.py](../awtrix3/sun_location.py) estimates sunrise/sunset and
  daylight percentage.

## Battery arbitrage directory
- [../battery_arbitrage/battery_info.py](../battery_arbitrage/battery_info.py) reads
  Ecoworthy battery data over BLE.
- [../battery_arbitrage/main_arbitrage.py](../battery_arbitrage/main_arbitrage.py) decides
  charge or discharge from pricing.
- [../battery_arbitrage/test_code.py](../battery_arbitrage/test_code.py) exercises BLE
  battery queries for debugging.

## HTML directory
- [../html/comed.py](../html/comed.py) CGI page showing ComEd pricing and links.
- [../html/fullhouse.py](../html/fullhouse.py) CGI page with solar, usage, and price plot.
- [../html/generate_comed_html.py](../html/generate_comed_html.py) writes a static ComEd
  HTML page.
- [../html/house.py](../html/house.py) CGI page combining solar, usage, Ecobee, and ComEd
  data.
- [../html/test.py](../html/test.py) legacy CGI test script.

## Legacy lib_oled96 directory
- [../legacy/lib_oled96/lib_oled96.py](../legacy/lib_oled96/lib_oled96.py) I2C OLED driver
  for SSD1306 displays.
- [../legacy/lib_oled96/example1-oled96-rpi.py](../legacy/lib_oled96/example1-oled96-rpi.py)
  Raspberry Pi OLED example.
- [../legacy/lib_oled96/example2-oled96-rpi.py](../legacy/lib_oled96/example2-oled96-rpi.py)
  extended Raspberry Pi OLED example.
- [../legacy/lib_oled96/example2-oled96-vgpio.py](../legacy/lib_oled96/example2-oled96-vgpio.py)
  virtual GPIO OLED example.
- [../legacy/lib_oled96/ReadMe.md](../legacy/lib_oled96/ReadMe.md) upstream notes and
  setup guidance for the OLED library.

## Legacy directory
- [../legacy/__init__.py](../legacy/__init__.py) marks the legacy scripts as a Python
  package.
- [../legacy/logEnergy.py](../legacy/logEnergy.py) logs PECMAC125A usage with solar
  production samples.
- [../legacy/moneroMinerControl-comed.py](../legacy/moneroMinerControl-comed.py) enables or
  disables mining based on ComEd prices.
- [../legacy/wemoPlug-comed.py](../legacy/wemoPlug-comed.py) legacy WeMo plug controller
  with a simplified cutoff model.
- [../legacy/wemoPlug-comed-old.py](../legacy/wemoPlug-comed-old.py) legacy WeMo charging
  controller with fixed thresholds.
- [../legacy/PECMAC125A.py](../legacy/PECMAC125A.py) reads PECMAC125A I2C current data and
  logs it.
- [../legacy/readSMBus.py](../legacy/readSMBus.py) reads PECMAC125A usage data via SMBus.
- [../legacy/smartReadUsage.py](../legacy/smartReadUsage.py) combines SMBus reads and solar
  data into usage summaries.
- [../legacy/plot_usage.py](../legacy/plot_usage.py) plots today's usage log as a CGI
  image.
- [../legacy/plot_yesterday_usage.py](../legacy/plot_yesterday_usage.py) plots yesterday's
  usage log as a CGI image.
- [../legacy/whilePEC.sh](../legacy/whilePEC.sh) runs
  [../legacy/logEnergy.py](../legacy/logEnergy.py) in a loop with a fixed delay.
