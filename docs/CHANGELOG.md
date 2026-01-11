# Changelog

## 2026-01-10
- NFL league mode uses fixed-width layout: 9px team boxes + 14px center time area.
- NFL league mode always uses 2-letter team abbreviations (never 3).
- NFL countdown uses `'` for hours and `"` for minutes (e.g., `15'` or `45"`).
- NFL countdown shows days for 4+ days, hours for 2+ hours, minutes otherwise.
- NFL uses both ESPN team colors: brighter as background, darker as text (no white/black fallback).
- Improved time centering in NFL layout (round-up bias for odd pixel differences).
- Add [`awtrix3/sports_countdown.py`](../awtrix3/sports_countdown.py) for sports game countdown display.
- Add [`awtrix3/sports_teams.yaml`](../awtrix3/sports_teams.yaml) config for team tracking with enable/disable flags.
- Add [`awtrix3/AWTRIX3_PYTHON_SPEC.md`](../awtrix3/AWTRIX3_PYTHON_SPEC.md) describing AWTRIX script conventions.
- Document text spacing/width budgeting patterns used by `sports_countdown.py` and `display_date.py`.
- Support league-wide countdown entries (for example, "next NFL game") alongside team-specific countdown apps.
- Add compact single-screen league matchup+countdown display via `show_matchup: true` (for example, `[LA] 7H [Ca]`).
- Auto-fit league matchup boxes to use 3-letter abbreviations when they fit (for example, `[LAC] 7H [Car]`).
- Fall back to 2-letter abbreviations when wide letters (like `W`/`M`) prevent 3-letter boxes from fitting.
- Prefer brighter team color for box background with darker text when possible (better contrast when one color is black).
- Clamp `<1H` countdown token to `1H` (no minutes displayed).
- Round league countdown tokens up (ceiling) so the display doesn't understate time remaining (for example, `150m` -> `3H`).
- Add `--debug` flag to `sports_countdown.py` for verbose color/layout/ESPN data decisions.
- Document upstream AWTRIX font glyph reference link in the AWTRIX spec.
- Document AWTRIX display constraints and ESPN API fields relevant to future sports countdown expansions.
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
