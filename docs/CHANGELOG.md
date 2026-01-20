# Changelog

## 2026-01-20
- Replace non-ASCII symbols in AWTRIX authoring/spec docs with ASCII-safe diagrams and markers.
- Fix pyflakes findings by removing unused imports, replacing legacy `file()` calls with `open()`, and updating Python 3 print syntax.
- Document ASCII-only table and diagram rules in `docs/MARKDOWN_STYLE.md`.

## 2026-01-16
- Refresh `README.md` with a standardized doc map and quick start.
- Add `README.md` with repo overview, documentation links, and a quick start.
- Add [INSTALL.md](INSTALL.md) and [USAGE.md](USAGE.md) covering dependencies,
  entry points, and configuration files.
- Update [FILES.md](FILES.md) to list the new documentation.
- Add [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) with component and data flow notes.
- Add [FILE_STRUCTURE.md](FILE_STRUCTURE.md) with a directory map and conventions.
- Fix `apps/checkPrices-comed.py` plot alpha to use a valid 0-1 range.
- Add architecture and file structure links to `README.md`.
- Link file references across `README.md` and docs for easier navigation.
- Normalize internal Markdown link text to match target file paths.

## 2026-01-14
- Resolve merge conflict artifacts in `AGENTS.md`.
- Add per-file progress markers to `tests/run_ascii_compliance.sh`: green `.` for clean, yellow `+` for auto-fixed, red `!` for unfixable issues.
- Include the offending character after the U+ codepoint in `tests/check_ascii_compliance.py` output when printable.
- Auto-fix common arrow characters in `tests/check_ascii_compliance.py` (for example, `\u2192` to `->`, `\u2190` to `<-`).
- Report the total number of files with ASCII errors in `tests/run_ascii_compliance.sh`, listing paths when fewer than five.
- Convert the ASCII compliance runner to `tests/run_ascii_compliance.py`, leaving `tests/run_ascii_compliance.sh` as a wrapper.
- Add top-5 Unicode character counts to the ASCII compliance report, plus per-file error counts when five or fewer files fail.
- Add [../awtrix3/AWTRIX3_AUTHORING_GUIDE.md](../awtrix3/AWTRIX3_AUTHORING_GUIDE.md) documenting how to author AWTRIX 3 custom app scripts in this repo.
- Sports schedule league mode shows weekday tokens (for example, `Sat`) instead of hour counts for future games, and shows a compact time token (for example, `3p`) for games happening today.
- Rename `awtrix3/sports_countdown.py` to `awtrix3/sports_schedule.py` and update callers.
- Remove remaining "countdown" naming in `awtrix3/` (function names, comments, and app name suffixes) in favor of schedule/next-game terms.

## 2026-01-10
- Football leagues (NFL, NCAAF) use fixed-width layout: 9px team boxes + 14px center time area.
- Football leagues always use 2-letter team abbreviations (never 3).
- Football countdown shows game time (e.g., `I2p`, `3a`) when under 24 hours away.
- Football countdown shows days for 4+ days, hours with `'` otherwise (e.g., `36'`).
- Football time display uses 'I' instead of '1' for narrow display (AWTRIX 'I' is 1px wide).
- Team abbreviations use serifed 'I' (3px) when no M/W present, narrow 'I' (1px) otherwise.
- Football leagues prefer primary ESPN color as background; swap to alternate only if R+G+B < 128.
- Add `--debug` summary table showing team colors, RGB values, and background selection.
- Improved time centering in football layout (round-up bias for odd pixel differences).
- Add College Football Playoffs (CFP) league mode entry to `sports_teams.yaml`.
- Add [../awtrix3/sports_schedule.py](../awtrix3/sports_schedule.py) for sports game countdown display (originally added as `sports_countdown.py`).
- Add [../awtrix3/sports_teams.yaml](../awtrix3/sports_teams.yaml) config for team tracking with enable/disable flags.
- Add [../awtrix3/AWTRIX3_PYTHON_SPEC.md](../awtrix3/AWTRIX3_PYTHON_SPEC.md) describing AWTRIX script conventions.
- Document text spacing/width budgeting patterns used by `sports_schedule.py` and `display_date.py`.
- Support league-wide countdown entries (for example, "next NFL game") alongside team-specific countdown apps.
- Add compact single-screen league matchup+countdown display via `show_matchup: true` (for example, `[LA] 7H [Ca]`).
- Auto-fit league matchup boxes to use 3-letter abbreviations when they fit (for example, `[LAC] 7H [Car]`).
- Fall back to 2-letter abbreviations when wide letters (like `W`/`M`) prevent 3-letter boxes from fitting.
- Prefer brighter team color for box background with darker text when possible (better contrast when one color is black).
- Clamp `<1H` countdown token to `1H` (no minutes displayed).
- Round league countdown tokens up (ceiling) so the display doesn't understate time remaining (for example, `150m` -> `3H`).
- Add `--debug` flag to `sports_schedule.py` for verbose color/layout/ESPN data decisions.
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
- Add [docs/FILES.md](docs/FILES.md) with a per-file guide for the repo.
- Move PECMAC125A tooling, SMBus logger, and miner scripts into `legacy/`.
- Add `apps/`, `energylib/`, and `plots/` directories with compatibility wrappers.
- Move usage plotting and usage readers into `legacy/`.
- Update CGI usage links to point at the legacy usage plots.
- Replace wrapper `import *` usage with explicit module proxies.
- Fix AWTRIX wrappers to add repo root to `sys.path` for `energylib` imports.
- Remove compatibility wrappers and update imports to use `energylib` directly.
- Update app and plot entrypoints to resolve `energylib` from the repo root.
- Point `run_all_screens.sh` at the `apps/` entrypoints.
- Add [pip_requirements.txt](pip_requirements.txt) and `Brewfile` for repo dependencies.
- Comment out legacy-only Python dependencies in [pip_requirements.txt](pip_requirements.txt).
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
- Fix regex escape warnings in [energylib/commonlib.py](energylib/commonlib.py).
- Add commentary on the multi-plug WeMo decision logic.
- Add [docs/wemoPlug-comed-multi.md](docs/wemoPlug-comed-multi.md) documenting the decision flow.
- Move documentation guides into `docs/`.
