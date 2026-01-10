# AWTRIX 3 Python scripts spec

This folder contains small Python scripts that generate AWTRIX "custom app" payloads and (optionally) send
them to an AWTRIX 3 display device.

This spec describes the conventions used here and the recommended pattern for adding new scripts, especially
when extending `sports_countdown.py`.

## Goals

- Keep each script single-purpose: "compile data for one AWTRIX app".
- Make scripts safe to run locally via `--dry-run` without sending anything.
- Keep the AWTRIX device responsive by rate limiting and keeping payloads small.
- Prefer deterministic layout on the 32x8 canvas (avoid scroll unless necessary).

## Display constraints

This repo assumes the 32x8 display is the limiting factor. When adding new apps, optimize for:

- Single-line readability (no multi-row layouts).
- Minimal use of `draw` primitives (complex drawing is hard to iterate and can be costly on-device).
- No custom logos; avoid solutions that require storing lots of icon assets.
- Avoid pixel-drawn "letters as logos" unless it is truly necessary; prefer text-only identifiers.

## Directory contents

- `send_price.py` is the orchestrator that calls the other scripts and sends each payload to AWTRIX.
- Payload generator scripts typically provide:
  - `compile_*()` or `get_*_data()` which returns an AWTRIX payload dict (or `None` to skip).
  - `send_to_awtrix(app_data)` for standalone sending.
  - `main()` + `argparse` with a `--dry-run` flag.
- `icon_draw.py` holds shared icon IDs and helper draw primitives (for example, arrows).
- Configuration files used by scripts:
  - `api.yml` for AWTRIX device connection details.
  - `sports_teams.yaml` for sports countdown team configuration.
  - `garmin_login.yml` for Garmin Connect credentials (used by `display_garmin_connect.py`).

## AWTRIX API conventions

### Endpoint and app naming

- Scripts use the AWTRIX "custom app" endpoint:
  - `POST http://<ip>/api/custom?name=<app_name>`
- `app_name` should be stable so the AWTRIX device updates the same app rather than creating many apps.
- For multi-entity apps (for example, per-team countdown), use a deterministic name derived from config, such as
  `<SHORT>Countdown`.

### Authentication and secrets

- Current scripts load credentials from `api.yml` and use HTTP basic auth.
- Do not print credentials in logs and do not include real credentials in documentation examples.
- If adding new config files with secrets, prefer keeping them out of git (for example via `.gitignore`) and
  consider reading from environment variables first.

### Rate limiting

- Avoid sending many payloads back-to-back without delay.
- Prefer a small randomized sleep between requests when calling external APIs or AWTRIX, to reduce burst load.

## AWTRIX payload format (custom app)

The scripts build a Python `dict` that is posted as JSON. Common keys used in this repo:

- `name`: App name (also mirrored in the query string name).
- `text`: Main text to show (keep it short to avoid scroll).
- `icon`: Numeric icon ID (see `icon_draw.awtrix_icons` and `sports_teams.yaml` league icons).
- `color`: Text color; either `#RRGGBB` or `[r, g, b]` depending on usage.
- `textCase`: Use `2` when mixed/lowercase should be preserved.
- `repeat`: How many loops to repeat.
- `duration`: Seconds to show per loop.
- `lifetime`: Seconds the app remains active before expiring (should match update cadence).
- `stack`: When `True`, the app stacks nicely with other apps in the loop.
- `center` / `noScroll` / `scrollSpeed`: Display behavior toggles.
- `progress` / `progressC`: Optional progress bar and color.
- `draw`: Optional list of draw commands that render on the 32x8 display.

### Draw commands

The AWTRIX display is 32 pixels wide (x=0..31) and 8 pixels tall (y=0..7).

Common draw primitives used here:

- `df`: Draw filled rectangle: `[x, y, width, height, color]`
- `dt`: Draw text: `[x, y, text, color]`
- `dl`: Draw line: `[x0, y0, x1, y1, color]`

Layout is constrained and font widths vary; for tight layouts, compute approximate text widths (see
`display_date.py` and `sports_countdown.py`) and prefer fixed-position elements over auto-centering.

## Text spacing and layout (32x8)

Text spacing is the most common source of "why does this look wrong" on AWTRIX because the built-in font is
not monospaced and the display is only 32 pixels wide.

### Approach used in this repo

Both `display_date.py` and `sports_countdown.py` handle spacing by approximating character widths and then
budgeting pixels explicitly:

- Treat most characters as 3px wide.
- Treat `M`/`W` (and lowercase variants) as 5px wide.
- Treat space as 1px wide.
- Add a 1px inter-character gap when computing multi-character widths.

This approximation is "good enough" for consistently placing elements like:

- A right-aligned box (for example, the team letter box in `sports_countdown.py`).
- A month string that starts after a weekday prefix (as in `display_date.py`).

### Rules of thumb

- Prefer non-scrolling text (`noScroll: True`) and shorten strings until they fit.
- Compute x positions from a pixel budget (for example, `available_width = 32 - right_box_width`).
- Keep "optional" separators (like a space between tokens) conditional, and drop them when width is tight.
- When adding new display variants, decide the fixed anchors first (right box, left icon), then fill the
  remaining middle space.
- For the canonical AWTRIX font glyphs (useful when tuning per-letter spacing), see the upstream header:
  [AwtrixFont.h](https://github.com/Blueforcer/awtrix3/blob/2f65f1f4/src/AwtrixFont.h#L58-L521).

## ESPN API data available

When expanding `sports_countdown.py`, the ESPN API endpoints determine what metadata is available for display.

### League scoreboard endpoint (best for matchup + team metadata)

`GET https://site.api.espn.com/apis/site/v2/sports/<sport_path>/scoreboard`

For each event, you typically get:

- `event.date` (UTC ISO8601, with `Z` suffix) for countdown calculations.
- `event.name` and `event.shortName` (human readable).
- `competition.status.type` including `description`, `detail`, `shortDetail`, and `state`.
- `competition.competitors[]`:
  - `homeAway` (`home` or `away`)
  - `score` (string)
  - `team.abbreviation` (for example, `LAR`, `CAR`)
  - `team.location` (for example, `Los Angeles`, `Carolina`) which is useful for compact 2-letter codes (`LA`,
    `CA`) without hardcoding per-team rules
  - `team.displayName` and `team.shortDisplayName`
  - `team.color` and `team.alternateColor` (hex without a leading `#`, for example `003594`)

Notes:

- `team.color` and `team.alternateColor` are present here for many leagues and are the closest thing to
  "team colors" without maintaining a local mapping.
- Some colors are very dark on the AWTRIX background; if using them directly, apply a minimum brightness
  adjustment (see `ensure_min_brightness()` in `sports_countdown.py`).
- If you do not want to color by team at all, a simple alternative is to color by urgency (time remaining), and
  encode the matchup as compact text (for example, `LA7Ca`) derived from `team.location` with no hardcoded map.

### Team schedule endpoint (good for "next game for this team", but minimal metadata)

`GET https://site.api.espn.com/apis/site/v2/sports/<sport_path>/teams/<TEAM_ID>/schedule`

This is the current team-focused endpoint, but competitor `team` objects may omit `color`/`alternateColor`.
If you need team colors without hardcoding, prefer:

- League scoreboard data (above), or
- A separate lookup per team via the team endpoint (below), with caching.

### Team endpoint (team metadata lookup, cacheable)

`GET https://site.api.espn.com/apis/site/v2/sports/<sport_path>/teams/<TEAM_ID>`

This typically returns `team.color` / `team.alternateColor` along with names and location and is suitable for a
local on-disk cache to avoid repeated network calls.

## Script structure (recommended for new scripts)

### Minimal API

Each new app script should expose a payload generator function that does not perform network I/O by default:

- `compile_<thing>_data(...) -> dict | None`

If it returns `None`, callers treat that as "skip sending".

If a module naturally produces multiple apps (for example, one app per configured entity), prefer returning a
list:

- `compile_<thing>_apps(...) -> list[dict] | None`

### CLI behavior

- Add `argparse` with `--dry-run` (`-d`) to print the payload and exit without sending.
- Keep argparse minimal; only add flags users will actually change between runs.

### Sending

If the script is intended to be run standalone, provide:

- `get_api_config()` that loads `api.yml` from the script directory.
- `send_to_awtrix(app_data)` that POSTs to the AWTRIX endpoint.

When the script is primarily called by `send_price.py`, it is OK if `send_price.py` does the sending, but keep
the payload format identical so the script can be promoted to standalone later if desired.

### Imports and repo root

If a script imports `energylib` and it needs to be runnable directly, add the repo root to `sys.path` the way
`comed_price_display.py` and `solar_display.py` do.

## Adding a new app to `send_price.py`

To integrate a new payload generator into the orchestrator:

1. Import the new module in `send_price.py`.
2. Call the module's `compile_*()` function in `main()`.
3. Pass its returned dict to `send_to_awtrix()` (skip if `None`).
4. Keep an inter-send delay to avoid overwhelming the AWTRIX API.

## Sports countdown expansion guide

`sports_countdown.py` is the most likely script to expand because it talks to external schedule APIs and needs
to present more data than fits comfortably on a 32x8 display.

### Current behavior (high level)

- Loads enabled entries from `sports_teams.yaml` (team entries and optional league-wide entries).
- Skips leagues that are configured as off-season via `active_months`.
- Fetches each entry's next game/race from a league-specific API.
- Renders one compact countdown payload per enabled entry.
- Optionally draws a "letter-in-box" element on the right side to help identify the entry.

### Team vs league entries

`sports_teams.yaml` entries default to team mode (using a per-team schedule endpoint). If `mode: league` is set,
the script uses the ESPN league scoreboard endpoint and shows a countdown to the next game in that league,
which is useful when you want both:

- A team-specific countdown (for example, BEARS), and
- A league-wide "next game" countdown (for example, NFL).

For league entries, `show_matchup: true` switches the payload text to a compact single-line string that combines
matchup identity and urgency without needing logos, draw commands, or team-specific hardcoded colors.

Example: for a Los Angeles team at Carolina, show `LA7Ca` where `7` is a single numeric countdown value.

If you want spaces and team colors, render it as a single screen with draw boxes:

- Format: `[LA] 7H [Ca]` (two colored boxes and a center countdown token).
- Source: `team.location` for `LA` / `Ca`, and `team.color` + `team.alternateColor` for colors (no hardcoded map).
- Color rule: prefer the brighter of `color`/`alternateColor` for the box background and the darker for the text;
  if both colors are dark, use a dark background and brighten the text to keep it readable.

Implementation notes:

- Prefer `team.abbreviation` (often 3 letters like `LAC`) when it fits; fall back to 2-letter `team.location`
  codes when the pixel budget is tight.
- Auto-fit by reducing box padding and inter-item gaps rather than changing fonts or adding scroll.
- If `W`/`M` make 3-letter labels too wide, fall back to 2-letter abbreviations (for example, `WA`, `Mi`).
- Token rule: show only `Xd` or `nH` (no minutes); round up (ceiling) so it never understates time remaining,
  and clamp `<1H` to `1H` rather than showing `0H`.

Debugging:

- `sports_countdown.py --dry-run --debug` prints the ESPN team fields used (abbreviation/location/colors), the
  label candidates tried, and the chosen padding/gap/x positions for the final draw layout.
- With `--debug`, the league countdown token also prints the raw seconds/hours used for the ceiling decision.

### Common challenges

- Timezones: ESPN data is UTC; displayed time/countdown should be computed consistently.
- External API reliability: handle timeouts, non-200 responses, and schema changes without crashing.
- Rate limiting: multiple teams can trigger many calls; cache and/or back off to avoid transient failures.
- Seasonality: off-season leagues should avoid any API traffic (use `active_months` and/or last-updated cache).
- Layout: 32x8 is extremely tight; "nice" UI requires careful width budgeting and contrast choices.
- Stability: app names must stay stable; changing names creates orphan apps on the device.

### Recommended future enhancements

- Add a small on-disk cache (for example JSON) keyed by team+date, with a TTL, to cut API calls.
- Support rotation modes:
  - "soonest only" (current behavior).
  - "rotate enabled teams" (one per update).
  - "pin team" (show a specific team only).
- Improve event selection:
  - Filter out postponed/canceled events.
  - Prefer "next scheduled" over "last completed" when schedules include both.
- Add display variants that remain non-scrolling:
  - `XdYh` or `HhMM` countdown (already used), plus optional opponent abbreviation.
  - Optional home/away marker via a tiny glyph in `draw`.
- Keep config backwards compatible; new fields should be optional with sensible defaults.
