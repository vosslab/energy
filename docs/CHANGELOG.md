# Changelog

## 2026-01-10
- Add [`awtrix3/sports_countdown.py`](../awtrix3/sports_countdown.py) for sports game countdown display.
- Add [`awtrix3/sports_teams.yaml`](../awtrix3/sports_teams.yaml) config for team tracking with enable/disable flags.
- Support ESPN API for NFL, NBA, MLB, NHL, WNBA leagues.
- Support Ergast API for Formula 1 race schedule.
- Add `active_months` config to skip API calls for off-season leagues.
- Config file lookup checks CWD first, then script directory.
- Add `--dry-run` (`-d`) flag to all AWTRIX scripts for testing without sending.
- Add letter-in-box display mode with dynamic box width based on letter.
- Add `letter`, `letter_color`, `box_color`, `text_color` config options.
- Layout: `[League Icon] countdown [Team Letter Box]`.
- Compact time format `7:25` instead of `7h 25m`.
- Fix duplicate `center` key in `display_date.py`.

## 2025-12-21
- Add argparse flags for WeMo debug, refresh timing, and plug IP overrides.
- Add WeMo connection diagnostics to the multi-plug controller.

## 2025-12-20
- Add [`docs/FILES.md`](docs/FILES.md) with a per-file guide for the repo.
- Move PECMAC125A tooling, SMBus logger, and miner scripts into `legacy/`.
- Add `apps/`, `energylib/`, and `plots/` directories with compatibility wrappers.
- Move usage plotting and usage readers into `legacy/`.
- Update CGI usage links to point at the legacy usage plots.
- Replace wrapper `import *` usage with explicit module proxies.
- Fix AWTRIX wrappers to add repo root to `sys.path` for `energylib` imports.
- Remove compatibility wrappers and update imports to use `energylib` directly.
- Update app and plot entrypoints to resolve `energylib` from the repo root.
- Point `run_all_screens.sh` at the `apps/` entrypoints.
<<<<<<< HEAD
- Add [`pip_requirements.txt`](pip_requirements.txt) and `Brewfile` for repo dependencies.
- Comment out legacy-only Python dependencies in [`pip_requirements.txt`](pip_requirements.txt).
- Add clarifying comments across the `awtrix3/` scripts.
- Improve AWTRIX date spacing and add subtle weekday/month color accents.
- Update AWTRIX weekday color palette to the provided day-specific colors.
- Update AWTRIX month color palette to the provided month-specific colors.
- Annotate AWTRIX weekday/month color hex values with approximate color names.
- Deepen November/December AWTRIX month colors for higher saturation.
- Add `apps/wemoPlug-comed-multi.py` for multi-plug support using the old2 pricing logic.
- Move legacy WeMo scripts to `legacy/`.
- Add ComEd library comments and replace `sys.exit()` with exceptions.
- Make ComEd cache writes atomic to prevent partial reads.
- Fix regex escape warnings in [`energylib/commonlib.py`](energylib/commonlib.py).
- Add commentary on the multi-plug WeMo decision logic.
- Add [`docs/wemoPlug-comed-multi.md`](docs/wemoPlug-comed-multi.md) documenting the decision flow.
- Move documentation guides into `docs/`.
