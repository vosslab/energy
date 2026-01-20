# AWTRIX 3 Python scripts spec

This folder contains small Python scripts that generate AWTRIX "custom app" payloads and (optionally) send
them to an AWTRIX 3 display device.

This spec describes the conventions used here and the recommended pattern for adding new scripts, especially
when extending `sports_schedule.py`.

## When to read what

- **This spec**: Read this for repo conventions, required patterns, and constraints ("this is how we do it here").
- **[AWTRIX3_AUTHORING_GUIDE.md](AWTRIX3_AUTHORING_GUIDE.md)**: Read this for practical how-to: templates,
  examples, layout tricks, and step-by-step instructions for building a new app.
- **[../docs/PYTHON_STYLE.md](../docs/PYTHON_STYLE.md)**: Read this for general Python style conventions
  (tabs, imports, argparse patterns) used across the repo.

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
  - `sports_teams.yaml` for sports schedule team configuration.
  - `garmin_login.yml` for Garmin Connect credentials (used by `display_garmin_connect.py`).

## AWTRIX API conventions

### Endpoint and app naming

- Scripts use the AWTRIX "custom app" endpoint:
  - `POST http://<ip>/api/custom?name=<app_name>`
- `app_name` should be stable so the AWTRIX device updates the same app rather than creating many apps.
- For multi-entity apps (for example, per-team next-game entries), use a deterministic name derived from config,
  such as `<SHORT>NextGame`.

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
`display_date.py` and `sports_schedule.py`) and prefer fixed-position elements over auto-centering.

## Text spacing and pixel budgeting

**This is the hardest part of AWTRIX development.** Every new coder gets surprised by spacing issues.
Read this section carefully before writing layout code.

### Why spacing is hard: the root cause

AWTRIX uses a **variable-width bitmap font**. This has two critical implications:

1. **Character widths vary dramatically**: `I` is 1px, most letters are 3px, `W` and `M` are 5px.
   The common assumption that "7 characters fit" is wrong-both strings below have 7 characters:
   - `IIIIIII` = 7x1px + 6 gaps = **13px** (fits easily)
   - `WMWMWMW` = 7x5px + 6 gaps = **41px** (overflows badly)

2. **Scroll triggers unpredictably**: AWTRIX scrolls when computed text width exceeds available space.
   Because widths vary, you cannot eyeball whether text will scroll-you must compute it.

The only reliable approach is **explicit pixel budgeting**: compute widths, allocate space, verify fit.

**Width measurement convention:** We measure width as glyph widths plus 1px per inter-character gap.
For example, `"Hi"` = H(3px) + i(1px) + 1 gap = **5px total**.

### The canonical font reference

For exact glyph widths when tuning per-character spacing, see the upstream font header:
[AwtrixFont.h](https://github.com/Blueforcer/awtrix3/blob/2f65f1f4/src/AwtrixFont.h#L58-L521)

This is the source of truth. Our approximations (below) are "good enough" for most layouts, but consult
the header when you need pixel-perfect placement.

### Font caveats and limitations

The AWTRIX bitmap font has quirks that will bite you:

**Case sensitivity:**
- Uppercase and lowercase have **different widths** (e.g., `W` = 5px vs `w` = 5px, but `I` = 1px vs `i` = 1px)
- Use `textCase: 2` in payload to preserve mixed case; default may force uppercase

**Punctuation:**
- Narrow (1px): `. , : ; ! ' "`
- Wider (3-4px): `@ # $ % &`
- Test brackets and parentheses explicitly

**Non-ASCII characters:**
- **Not reliably supported.** The bitmap font has a limited character set.
- Accented characters (e, n, u) may render as boxes or nothing
- Emoji and Unicode symbols will not work
- **Fallback:** Strip non-ASCII before display:
  ```python
  import unicodedata
  def ascii_only(text: str) -> str:
      return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
  ```

**Characters that do work:**
- cent sign - commonly used for prices (~3px)
- degree sign - for temperatures (~2px)
- Basic math: `+ - * / = < >`

**When in doubt:** Test on the actual device. Simulators may not match hardware rendering.

### The spacing contract (this repo's approach)

All scripts in this repo follow the same spacing contract:

**Step 1: Approximate character widths**
```
Width 5px: M, W, m, w
Width 3px: Most letters and digits (A-Z, a-z, 0-9)
Width 2px: 1, j
Width 1px: I, i, l, !, ., ,, :, ', space
Gap: 1px between each character
```

**Step 2: Allocate the 32px budget**
```
+-------------------------------------------------------------+
| [icon: 8px] [gap: 1px] [content: variable] [box: 7-9px]     |
|     ^                        ^                    ^         |
|   optional               fills remaining       optional     |
|   (left anchor)            space             (right anchor) |
+-------------------------------------------------------------+

Total: 32px
- Icon (if used): ~8px (icons are 8x8, but some have transparent edges)
- Icon-to-text gap: 1px
- Right-side box (if used): 7-9px depending on content
- Content: whatever remains
```

**Step 3: Compute, don't guess**
```python
def estimate_width(text: str) -> int:
    WIDTHS = {'M': 5, 'W': 5, 'm': 5, 'w': 5, 'I': 1, 'i': 1, 'l': 1,
              '!': 1, '.': 1, ',': 1, ':': 1, "'": 1, ' ': 1, '1': 2, 'j': 2}
    chars = sum(WIDTHS.get(c, 3) for c in text)
    gaps = max(0, len(text) - 1)
    return chars + gaps
```

### Spacing knobs available in AWTRIX

These payload fields affect text placement. Use them for fine-tuning, not as primary layout tools:

| Field | Purpose | When to use |
|-------|---------|-------------|
| `textOffset` | Shifts text start position by N pixels | Final 1-2px nudges after computing layout |
| `center` | Centers text horizontally | Only for short, non-scrolling text with no icon |
| `pushIcon` | Controls icon position relative to text | When icon placement conflicts with text; values: `0` (fixed), `1` (push with text), `2` (push out on scroll) |
| `noScroll` | Prevents scrolling | **Always set `True`**, then shorten text to fit |

**Important**: `center` only works well for static text. If text might scroll, or if you have an icon,
use explicit `draw` commands with computed x positions instead.

### Best practices (the rules)

These rules exist because every violation has caused production bugs:

1. **Pick fixed anchors first, then fill remaining pixels.**
   Decide right-box width and icon presence before computing content width.

2. **Assume separators are optional.**
   Spaces, colons, and dashes are the first things to drop when tight on pixels.

3. **Prefer `noScroll: True`, then shorten until it fits.**
   Scrolling text is hard to read on 32x8. Static text is always better.

4. **Use `textOffset` and `pushIcon` for final nudges only.**
   If you need more than 2px adjustment, your layout math is wrong.

5. **Test with worst-case strings.**
   If your app shows team names, test with `MIAMI` and `WASHINGTON`, not `LA` and `NY`.

For practical worked examples of these rules, see
[AWTRIX3_AUTHORING_GUIDE.md#text-spacing-the-32x8-challenge](AWTRIX3_AUTHORING_GUIDE.md#text-spacing-the-32x8-challenge).

## ESPN API data available

When expanding `sports_schedule.py`, the ESPN API endpoints determine what metadata is available for display.

### League scoreboard endpoint (best for matchup + team metadata)

`GET https://site.api.espn.com/apis/site/v2/sports/<sport_path>/scoreboard`

For each event, you typically get:

- `event.date` (UTC ISO8601, with `Z` suffix) for time-to-game calculations.
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
  adjustment (see `ensure_min_brightness()` in `sports_schedule.py`).
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

### How to pick an endpoint

| Need | Best endpoint | Why |
|------|---------------|-----|
| Next game for a specific team | Team schedule | Direct query, minimal data |
| All games today/this week | League scoreboard | One call, full metadata |
| Team colors for display | League scoreboard or Team endpoint | Colors included |
| Opponent info | League scoreboard | Both teams in response |

### Fields we rely on (quick reference)

**From scoreboard (per competitor):**
- `team.abbreviation` -> 3-letter code (e.g., `LAR`)
- `team.location` -> city name for 2-letter fallback (e.g., `Los Angeles` -> `LA`)
- `team.color`, `team.alternateColor` -> hex without `#` (e.g., `003594`)
- `homeAway` -> `"home"` or `"away"`
- `score` -> string

**From event:**
- `date` -> UTC ISO8601 with `Z` suffix
- `status.type.state` -> `"pre"`, `"in"`, `"post"`

### Recommended caching strategy

ESPN endpoints are rate-limited and can be slow. A simple file-based cache cuts API calls significantly:

```python
import json
import time
from pathlib import Path

CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_TTL = 300  # 5 minutes

def get_cached(key: str) -> dict | None:
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        data = json.loads(cache_file.read_text())
        if time.time() - data["timestamp"] < CACHE_TTL:
            return data["payload"]
    return None

def set_cached(key: str, payload: dict) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{key}.json"
    cache_file.write_text(json.dumps({
        "timestamp": time.time(),
        "payload": payload,
    }))
```

Use case examples:
- Cache team metadata indefinitely (colors rarely change)
- Cache scoreboard for 5 minutes during games, longer off-season
- Key by `{league}_{team_id}_{date}` for schedule lookups

### Dark team colors: brightness floor

Many team colors are too dark to read on AWTRIX's black background. Apply a minimum brightness:

```python
def ensure_min_brightness(hex_color: str, min_brightness: int = 80) -> str:
    """Ensure color has minimum brightness (0-255 scale)."""
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    brightness = (r + g + b) // 3
    if brightness < min_brightness:
        factor = min_brightness / max(brightness, 1)
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
    return f"{r:02x}{g:02x}{b:02x}"
```

Rule of thumb: if `(r + g + b) / 3 < 80`, the color is probably invisible.

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

## Sports schedule expansion guide

`sports_schedule.py` is the most likely script to expand because it talks to external schedule APIs and needs
to present more data than fits comfortably on a 32x8 display.

### Current behavior (high level)

- Loads enabled entries from `sports_teams.yaml` (team entries and optional league-wide entries).
- Skips leagues that are configured as off-season via `active_months`.
- Fetches each entry's next game/race from a league-specific API.
- Renders one compact next-game payload per enabled entry.
- Optionally draws a "letter-in-box" element on the right side to help identify the entry.

### Team vs league entries

`sports_teams.yaml` entries default to team mode (using a per-team schedule endpoint). If `mode: league` is set,
the script uses the ESPN league scoreboard endpoint and shows a compact day/time token for the next game in that
league, which is useful when you want both:

- A team-specific next-game entry (for example, BEARS), and
- A league-wide "next game" entry (for example, NFL).

For league entries, `show_matchup: true` switches the payload text to a compact single-line string that combines
matchup identity and urgency without needing logos, draw commands, or team-specific hardcoded colors.

Example: for a Los Angeles team at Carolina, show `LASaCa` where `Sa` is the weekday token (or `LA3pCa` for a
same-day game).

If you want spaces and team colors, render it as a single screen with draw boxes:

- Format: `[LA] Sa [Ca]` (two colored boxes and a center schedule token).
- Source: `team.location` for `LA` / `Ca`, and `team.color` + `team.alternateColor` for colors (no hardcoded map).
- Color rule: prefer the brighter of `color`/`alternateColor` for the box background and the darker for the text;
  if both colors are dark, use a dark background and brighten the text to keep it readable.

Implementation notes:

- Prefer `team.abbreviation` (often 3 letters like `LAC`) when it fits; fall back to 2-letter `team.location`
  codes when the pixel budget is tight.
- Auto-fit by reducing box padding and inter-item gaps rather than changing fonts or adding scroll.
- If `W`/`M` make 3-letter labels too wide, fall back to 2-letter abbreviations (for example, `WA`, `Mi`).
- Token rule: if the event is today (local), show a compact hour token like `3p`; otherwise show a weekday token
  like `Sa` or `Sat` based on the available pixel width.

Debugging:

- `sports_schedule.py --dry-run --debug` prints the ESPN team fields used (abbreviation/location/colors), the
  label candidates tried, and the chosen padding/gap/x positions for the final draw layout.
- With `--debug`, the token selection prints whether a weekday or time token was chosen.

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
  - Weekday/time tokens (for example `Sa`/`Sat` or `3p`), plus optional opponent abbreviation.
  - Optional home/away marker via a tiny glyph in `draw`.
- Keep config backwards compatible; new fields should be optional with sensible defaults.

## Troubleshooting and gotchas

Hard-won lessons from production use. Each entry follows: **Symptom -> Likely cause -> Fix**.

For basic display issues (app not appearing, text cut off, etc.), see the troubleshooting table in
[AWTRIX3_AUTHORING_GUIDE.md#troubleshooting](AWTRIX3_AUTHORING_GUIDE.md#troubleshooting).

### Timezone drift (wrong game times)

**Symptom:** Game time shows wrong hour, or "today" games appear as "tomorrow".

**Cause:** ESPN returns UTC timestamps (`2024-01-15T01:30Z`), but display logic uses local time inconsistently.

**Fix:** Always convert to local timezone before extracting day/hour:
```python
from datetime import datetime, timezone
import zoneinfo

def parse_espn_date(utc_string: str) -> datetime:
    """Parse ESPN UTC date and convert to local time."""
    utc_dt = datetime.fromisoformat(utc_string.replace("Z", "+00:00"))
    local_tz = zoneinfo.ZoneInfo("America/Chicago")  # or your timezone
    return utc_dt.astimezone(local_tz)
```

### External API failures (empty display, crashes)

**Symptom:** Script crashes or returns `None` unexpectedly. Display goes blank.

**Cause:** ESPN API returned non-200, timed out, or changed schema.

**Fix:** Wrap all external calls in try/except and return `None` gracefully:
```python
def fetch_scoreboard(league: str) -> dict | None:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"ESPN fetch failed: {e}")
        return None
```

### Rate limiting (intermittent failures)

**Symptom:** Script works sometimes, fails other times. ESPN returns 429 or connection resets.

**Cause:** Too many requests too fast, especially with multiple teams configured.

**Fix:**
1. Add random sleep before each API call: `time.sleep(random.uniform(0.5, 1.5))`
2. Implement caching (see [Recommended caching strategy](#recommended-caching-strategy))
3. Use `active_months` in config to skip off-season leagues entirely

### Orphan apps (old apps won't go away)

**Symptom:** Device shows stale apps that should have been replaced. Loop has duplicates.

**Cause:** App `name` changed between runs (e.g., included dynamic data like score or timestamp).

**Fix:**
1. Derive `name` from config, not runtime data: `f"{team_id}NextGame"` not `f"{team_id}_{score}"`
2. Delete orphans manually: `curl -X POST "http://<ip>/api/custom?name=OldAppName" -d '{}'`
3. Check loop state: `curl http://<ip>/api/loop`

### Invisible text (dark colors)

**Symptom:** Text appears but is unreadable or invisible on the display.

**Cause:** Team color is too dark (e.g., `000033` for dark blue).

**Fix:** Apply brightness floor before using team colors:
```python
# See ensure_min_brightness() in the ESPN section above
color = ensure_min_brightness(team_color, min_brightness=80)
```

### Scroll when you expected static

**Symptom:** Text scrolls even though content looks short enough.

**Cause:** Text is wider than it looks (variable-width font), or `noScroll` not set.

**Fix:**
1. Always set `"noScroll": True`
2. Use `estimate_text_width()` to verify fit (see AWTRIX3_AUTHORING_GUIDE.md)
3. Shorten text until `width <= 32 - icon_width - right_box_width`

### App appears then vanishes

**Symptom:** App shows briefly after script runs, then disappears from loop.

**Cause:** `lifetime` too short relative to cron interval.

**Fix:** Set `lifetime` to at least `refresh_interval + buffer`:
```python
# If cron runs every 5 minutes (300s), use 360s lifetime
"lifetime": 360
```
