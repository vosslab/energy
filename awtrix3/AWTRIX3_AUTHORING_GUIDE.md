# AWTRIX 3 authoring guide

This guide describes how to author AWTRIX 3 "custom app" scripts in `awtrix3/` based on the patterns used by
the existing scripts (for example `display_date.py`, `comed_price_display.py`, `solar_display.py`, and
`sports_schedule.py`).

## When to read what

- **This guide**: Read this for practical how-to: templates, examples, layout tricks, and step-by-step
  instructions for building a new app.
- **[AWTRIX3_PYTHON_SPEC.md](AWTRIX3_PYTHON_SPEC.md)**: Read this for repo conventions, required patterns,
  API reference, payload field definitions, and constraints.
- **[../docs/PYTHON_STYLE.md](../docs/PYTHON_STYLE.md)**: Read this for general Python style conventions
  (tabs, imports, argparse patterns) used across the repo.

## Quick start pattern

Most scripts in this folder follow this structure:

- A pure payload generator, usually named `compile_*()` or `get_*_data()`, that returns:
  - `dict` for one app payload, or
  - `list[dict]` for multiple app payloads, or
  - `None` to indicate "skip sending"
- Optional standalone sending helpers:
  - `get_api_config()` loads `api.yml` from this folder.
  - `send_to_awtrix(app_data)` posts one payload (and may also accept a list of payloads).
- A tiny CLI:
  - `--dry-run` prints the payload and does not send.
  - Some scripts add a `--config` or `--debug` flag when it is genuinely useful.

### Minimal single-app template

```python
#!/usr/bin/env python3

# Standard Library
import os
import argparse

# PIP3 modules
import yaml
import requests
from requests.auth import HTTPBasicAuth

#============================================
def compile_example_data() -> dict:
	data = {
		"name": "ExampleApp",
		"text": "Hi",
		"noScroll": True,
		"repeat": 20,
		"duration": 5,
		"stack": True,
		"lifetime": 120,
	}
	return data

#============================================
def get_api_config() -> dict:
	config_path = os.path.join(os.path.dirname(__file__), "api.yml")
	with open(config_path, "r") as f:
		return yaml.safe_load(f)

#============================================
def send_to_awtrix(app_data: dict | list[dict] | None) -> bool:
	"""Send one or more payloads to the AWTRIX device."""
	if app_data is None:
		print("No data to send")
		return False

	# Handle list of payloads recursively
	if isinstance(app_data, list):
		return all(send_to_awtrix(item) for item in app_data)

	config = get_api_config()
	url = f"http://{config['ip']}/api/custom?name={app_data.get('name', 'ExampleApp')}"
	response = requests.post(url, json=app_data, auth=HTTPBasicAuth(config["username"], config["password"]))

	if response.status_code != 200:
		print(f"Failed to send {app_data.get('name')}: {response.status_code} - {response.text}")
		return False
	return True

#============================================
def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Example AWTRIX app")
	parser.add_argument("-d", "--dry-run", dest="dry_run", action="store_true",
		help="Print payload without sending to device")
	return parser.parse_args()

#============================================
def main() -> None:
	args = parse_args()
	data = compile_example_data()
	print(f"AWTRIX Data: {data}")
	if not args.dry_run:
		send_to_awtrix(data)

#============================================
if __name__ == "__main__":
	main()
```

## Default payload checklist

Before shipping a new app, verify these three things that prevent 80% of display issues:

1. **Use `noScroll: True`** and shorten text until it fits (budget ~23px after icon, not characters)
2. **Set `lifetime` >= refresh interval + buffer** (e.g., 5-min cron -> `lifetime: 360`)
3. **Keep `name` stable and unique** across runs to avoid orphan apps

For the full list of payload fields, see [AWTRIX3_PYTHON_SPEC.md#awtrix-payload-format-custom-app](AWTRIX3_PYTHON_SPEC.md#awtrix-payload-format-custom-app).

## Payload timing: `lifetime` vs `duration`

The two timing fields are the most common source of confusion:

- `duration`: How many seconds the app displays per loop cycle before rotating to the next app.
- `lifetime`: How many seconds the app remains in the loop before expiring and being removed.

Set `lifetime` to be greater than or equal to your script's refresh interval (e.g., cron frequency).
For example, if a cron job runs every 5 minutes (300s), use `lifetime: 360` to allow some buffer.

### Units and timing reference

**All AWTRIX timing values are in seconds (integers), not milliseconds.**

| Field | Unit | Typical values | What happens if wrong |
|-------|------|----------------|----------------------|
| `duration` | seconds | 3-10 | Too short = flickers; too long = boring |
| `lifetime` | seconds | 120-600 | Too short = app vanishes between refreshes |
| `repeat` | count | 1-20 | How many times to loop before advancing |
| `scrollSpeed` | percentage | 50-100 | Only matters if scrolling (avoid scrolling) |

### Timing math with cron

```
cron interval:  5 minutes = 300 seconds
buffer:         60 seconds (for network delays, slow APIs)
lifetime:       300 + 60 = 360 seconds

Rule: lifetime >= cron_interval + buffer
```

**Common timing bugs:**

| Bug | Symptom | Fix |
|-----|---------|-----|
| `lifetime: 300` with 5-min cron | App briefly vanishes before refresh | Use `lifetime: 360` |
| `duration: 1` | App flickers, hard to read | Use `duration: 5` minimum |
| `lifetime: 30` | App appears then vanishes | Match lifetime to refresh interval |
| Using milliseconds | App vanishes instantly | Use seconds, not ms |

---

## Cookbook: 5 practical examples

Each example focuses on one idea. Copy, adapt, ship.

**Indentation note:** This repo uses **tabs** for Python indentation (see [../docs/PYTHON_STYLE.md](../docs/PYTHON_STYLE.md)).
The minimal template above uses tabs. Examples below use spaces for markdown readability-convert to tabs when pasting into code.

### Example 1: Hello world text app

The absolute minimum payload. Shows what fields you actually need.

```python
def compile_hello_data() -> dict:
    return {
        "name": "HelloWorld",      # Stable, unique identifier
        "text": "Hello",           # Keep short (< 7 chars)
        "noScroll": True,          # Prevent scrolling
        "duration": 5,             # Seconds per loop cycle
        "lifetime": 120,           # Seconds before expiring
    }
```

That's it. Five fields. Everything else is optional.

### Example 2: Draw-based layout (right badge + left text)

When you need precise control, use `draw` commands instead of `text`.

```python
def compile_badge_layout() -> dict:
    # Step 1: Define fixed anchor (right-side badge)
    badge_width = 9
    badge_x = 32 - badge_width  # x=23

    # Step 2: Fill remaining space with left-aligned content
    return {
        "name": "BadgeDemo",
        "text": "",  # Empty - we're using draw instead
        "noScroll": True,
        "duration": 5,
        "lifetime": 120,
        "draw": [
            # Background badge (renders first)
            {"df": [badge_x, 0, badge_width, 8, "#0066CC"]},
            # Badge text (renders on top)
            {"dt": [badge_x + 2, 1, "OK", "#FFFFFF"]},
            # Left-side content (in remaining 23px)
            {"dt": [0, 1, "Status", "#00FF00"]},
        ],
    }
```

Key insight: Anchor fixed elements first (right badge), then fill the remaining pixels.

### Example 3: Text width budgeting (the 32x8 pain cave)

When text must fit exactly, compute widths explicitly.

```python
CHAR_WIDTHS = {
    'M': 5, 'W': 5, 'm': 5, 'w': 5,  # Wide
    'I': 1, 'i': 1, 'l': 1, '1': 2,  # Narrow
    ' ': 1,                          # Space
    # Default: 3px
}

def estimate_width(text: str) -> int:
    """Width in pixels, including 1px inter-character gaps."""
    chars = sum(CHAR_WIDTHS.get(c, 3) for c in text)
    gaps = max(0, len(text) - 1)
    return chars + gaps

def compile_fitted_text(label: str, value: str) -> dict:
    # Step 1: Reserve right-side box (9px)
    box_width = 9
    box_x = 32 - box_width
    available = box_x - 1  # 22px for content

    # Step 2: Compute what fits
    full_text = f"{label}: {value}"
    if estimate_width(full_text) > available:
        # Try shorter version
        full_text = f"{label[0]}: {value}"
    if estimate_width(full_text) > available:
        # Last resort: value only
        full_text = value

    # Step 3: Place deterministically
    return {
        "name": "FittedText",
        "text": "",
        "noScroll": True,
        "duration": 5,
        "lifetime": 120,
        "draw": [
            {"df": [box_x, 0, box_width, 8, "#333333"]},
            {"dt": [box_x + 2, 1, "OK", "#FFFFFF"]},
            {"dt": [0, 1, full_text, "#00FF00"]},
        ],
    }
```

The pattern: fixed anchors first -> compute remaining width -> shorten until it fits.

### Example 4: Multi-app module

One script that returns multiple apps with stable names.

```python
def compile_sensor_apps(sensors: list[dict]) -> list[dict] | None:
    """Return one app per sensor, or None if no sensors configured."""
    if not sensors:
        return None

    apps = []
    for sensor in sensors:
        # Stable name derived from config, not runtime data
        app_name = f"{sensor['id']}Status"

        apps.append({
            "name": app_name,
            "text": f"{sensor['label']}: {sensor['value']}",
            "noScroll": True,
            "duration": 5,
            "lifetime": 300,
            "stack": True,
        })

    return apps

# Usage in main():
def main():
    args = parse_args()
    sensors = load_sensor_config()
    apps = compile_sensor_apps(sensors)

    if args.dry_run:
        print(f"Would send {len(apps) if apps else 0} apps")
        for app in (apps or []):
            print(f"  - {app['name']}: {app['text']}")
    else:
        send_to_awtrix(apps)  # Handles list automatically
```

Key insight: `name` must be stable (derived from config), not dynamic (derived from data).

### Example 5: Orchestrator integration

Adding a new module to `send_price.py`.

```python
# In send_price.py:

# 1. Import your module
from my_new_app import compile_my_data

# 2. In main(), call compile and send with delay
def main():
    # ... existing apps ...

    # Add your new app
    my_data = compile_my_data()
    if my_data is not None:
        send_to_awtrix(my_data)
        time.sleep(0.5)  # Rate limit: don't hammer the device

    # Debug: check what's in the loop
    response = requests.get(f"http://{config['ip']}/api/loop")
    print(f"Current loop: {response.json()}")
```

Remember:
- Keep an inter-send delay (0.5s is usually enough)
- Use `GET /api/loop` to verify your app appeared
- If the app doesn't show, check `lifetime` and `stack`

---

## Draw commands cookbook

The display is 32 pixels wide (x=0..31) and 8 pixels tall (y=0..7). For the basic draw command
reference, see [AWTRIX3_PYTHON_SPEC.md#draw-commands](AWTRIX3_PYTHON_SPEC.md#draw-commands).

Commands in `draw` render in order, so later commands can overwrite earlier pixels.

### Common draw commands

| Command | Syntax | Description |
|---------|--------|-------------|
| `df` | `{"df": [x, y, w, h, color]}` | Filled rectangle |
| `dt` | `{"dt": [x, y, text, color]}` | Text at position |
| `dl` | `{"dl": [x0, y0, x1, y1, color]}` | Line |
| `dp` | `{"dp": [x, y, color]}` | Single pixel |
| `dr` | `{"dr": [x, y, w, h, color]}` | Rectangle outline |

### Practical examples

**Text on colored background:**
```python
"draw": [
    {"df": [0, 0, 10, 8, "#FF0000"]},  # Red background box
    {"dt": [1, 1, "Hi", "#FFFFFF"]},   # White text on top
]
```

**Right-aligned label box (from `display_date.py`):**
```python
# Draw a 2-letter day box anchored to the right edge
box_width = 9
box_x = 32 - box_width  # x=23
"draw": [
    {"df": [box_x, 0, box_width, 8, "#0066CC"]},  # Blue box
    {"dt": [box_x + 1, 1, "Tu", "#FFFFFF"]},      # Day text
]
```

**Separator line:**
```python
# Vertical separator at x=15
{"dl": [15, 0, 15, 7, "#444444"]}
```

## Text spacing: the 32x8 challenge

**This section will save you hours of frustration.** Text spacing is the #1 source of bugs in AWTRIX
apps because the font is variable-width and the display is only 32 pixels wide.

For the underlying rules and spacing contract, see
[AWTRIX3_PYTHON_SPEC.md#text-spacing-and-pixel-budgeting](AWTRIX3_PYTHON_SPEC.md#text-spacing-and-pixel-budgeting).

### The core problem

You cannot eyeball whether text fits. Consider:
- `"IIIIIII"` -> 7 chars, but only **13px** (fits easily)
- `"WMWMWMW"` -> 7 chars, but **41px** (overflows badly)

The only solution: **compute widths explicitly**.

### Width estimation function

**Width measurement convention:** We measure width as glyph widths plus 1px per inter-character gap.

Copy this into your script (or import from `awtrix3/text_width.py` if available):

```python
# Layout constants - change in one place
ICON_WIDTH = 8      # Standard AWTRIX icon size
ICON_GAP = 1        # Gap after icon
DISPLAY_WIDTH = 32  # Total display width

CHAR_WIDTHS = {
    'M': 5, 'W': 5, 'm': 5, 'w': 5,           # Wide
    'I': 1, 'i': 1, 'l': 1, '!': 1, '.': 1,   # Narrow
    ',': 1, ':': 1, "'": 1, ' ': 1,
    '1': 2, 'j': 2,                            # Medium-narrow
    # Everything else: 3px
}

def estimate_width(text: str) -> int:
    """Pixel width including 1px inter-character gaps."""
    chars = sum(CHAR_WIDTHS.get(c, 3) for c in text)
    gaps = max(0, len(text) - 1)
    return chars + gaps
```

**Note:** If multiple scripts share this logic, consider creating `awtrix3/text_width.py` with these
definitions, then `from text_width import estimate_width, ICON_WIDTH` to prevent drift.

### Golden tests for width estimation

Use these to verify your `estimate_width()` implementation. If you change the width table,
re-run these tests to catch silent breakage:

```python
GOLDEN_TESTS = [
    # (string, expected_width, notes)
    # Width = sum(glyph widths) + (len - 1) gaps
    ("Hi", 5, "H(3) + i(1) + 1 gap = 5"),
    ("IIIIIII", 13, "7x1 + 6 gaps = 13"),
    ("WMWMWMW", 41, "7x5 + 6 gaps = 41"),
    ("5.2", 9, "5(3) + .(1) + 2(3) + 2 gaps = 9"),
    ("Jan 14", 20, "J(3)+a(3)+n(3)+sp(1)+1(2)+4(3) + 5 gaps = 20"),
    ("LA", 7, "L(3) + A(3) + 1 gap = 7"),
    ("LAR", 11, "L(3) + A(3) + R(3) + 2 gaps = 11"),
    ("MIAMI", 19, "M(5)+I(1)+A(3)+M(5)+I(1) + 4 gaps = 19"),
    ("3:45p", 17, "3(3)+:(1)+4(3)+5(3)+p(3) + 4 gaps = 17"),
    ("", 0, "empty string"),
]

def test_width_estimation():
    for text, expected, notes in GOLDEN_TESTS:
        actual = estimate_width(text)
        status = "PASS" if actual == expected else "FAIL"
        print(f"{status}: '{text}' -> {actual}px (expected {expected}px) [{notes}]")
```

Run `test_width_estimation()` after any changes to `CHAR_WIDTHS`.

### The fit_text() helper

Standard utility to pick the first format that fits. Use this instead of copy-pasting the pattern:

```python
def fit_text(max_px: int, candidates: list[str]) -> tuple[str, int]:
    """
    Return (chosen_text, margin) for the first candidate that fits.

    Args:
        max_px: Maximum available pixels
        candidates: List of strings in preference order (most readable first)

    Returns:
        (text, margin) where margin >= 0, or (last_candidate, negative_margin) if none fit
    """
    for text in candidates:
        width = estimate_width(text)
        margin = max_px - width
        if margin >= 0:
            return (text, margin)

    # None fit - return last candidate with negative margin
    last = candidates[-1] if candidates else ""
    return (last, max_px - estimate_width(last))

# Usage example:
available = 22
candidates = [
    "January 14",   # 36px - won't fit
    "Jan 14",       # 20px - fits with 2px margin
    "J14",          # 10px - backup
]
text, margin = fit_text(available, candidates)
print(f"Chose '{text}' with {margin}px margin")
```

**Benefits:**
- Consistent pattern across all scripts
- Returns margin for debugging
- Gracefully handles "nothing fits" case

### Worked example A: Icon + short text

**Goal:** Show electricity price with icon, must not scroll.

```python
def compile_price_display(price_cents: float) -> dict:
    # Step 1: Define pixel budget
    # Total: 32px
    # Icon: 8px (standard AWTRIX icon size)
    # Gap after icon: 1px
    # Available for text: 32 - 8 - 1 = 23px

    available = 23

    # Step 2: Format and measure
    text = f"{price_cents:.1f}¢"  # e.g., "5.2¢"
    width = estimate_width(text)   # "5.2¢" = 3+1+3+1+3 + 3 gaps = 14px ✓

    # Step 3: Verify fit
    if width > available:
        # Fallback: drop decimal
        text = f"{int(price_cents)}¢"

    # Step 4: Return payload
    return {
        "name": "ElecPrice",
        "icon": 12345,
        "text": text,
        "noScroll": True,  # ALWAYS
        "duration": 5,
        "lifetime": 300,
    }
```

**Math breakdown:**
```
Total:     32px
- Icon:     8px
- Gap:      1px
= Available: 23px

Text "5.2¢": 5(3) + .(1) + 2(3) + ¢(3) + 3 gaps(3) = 13px ✓
Text "12.5¢": 1(2) + 2(3) + .(1) + 5(3) + ¢(3) + 4 gaps(4) = 16px ✓
Text "EXPENSIVE": way over, needs fallback
```

### Worked example B: Right-side badge + left text

**Goal:** Show date with weekday badge on right.

```python
def compile_date_display(month: str, day: int, weekday: str) -> dict:
    # Step 1: Define fixed anchors FIRST
    badge_width = 9     # Fits 2-letter weekday + padding
    badge_x = 32 - badge_width  # x=23

    # Step 2: Compute available space for date text
    available = badge_x - 1  # 22px (1px gap before badge)

    # Step 3: Format date and measure
    date_text = f"{month} {day}"  # e.g., "Jan 14"
    width = estimate_width(date_text)

    # Step 4: Shorten if needed
    if width > available:
        date_text = f"{month[:3]} {day}"  # "January" -> "Jan"
    if estimate_width(date_text) > available:
        date_text = f"{month[0]}{day}"    # "J14" (last resort)

    # Step 5: Build draw commands
    return {
        "name": "DateDisplay",
        "text": "",  # Using draw instead
        "noScroll": True,
        "duration": 5,
        "lifetime": 300,
        "draw": [
            # Right badge (background first)
            {"df": [badge_x, 0, badge_width, 8, "#0066CC"]},
            {"dt": [badge_x + 2, 1, weekday[:2], "#FFFFFF"]},
            # Left date text
            {"dt": [0, 1, date_text, "#FFFFFF"]},
        ],
    }
```

**Math breakdown:**
```
Total:      32px
- Badge:     9px (at x=23)
- Gap:       1px
= Available: 22px for date

"January 14": J(3)+a(3)+n(3)+u(3)+a(3)+r(3)+y(3) + space(1) + 1(2)+4(3) + 9 gaps
            = 27 + 9 = 36px ✗ (too wide!)
"Jan 14":     J(3)+a(3)+n(3) + space(1) + 1(2)+4(3) + 5 gaps = 15 + 5 = 20px ✓
```

### Worked example C: Auto-fit with progressive shortening

**Goal:** Show matchup that adapts to team name lengths.

```python
def compile_matchup(home: str, away: str, time_token: str) -> dict:
    # Step 1: Fixed anchors
    icon_budget = 9      # Icon + gap
    badge_width = 7
    badge_x = 32 - badge_width
    available = badge_x - icon_budget - 1  # ~15px for matchup

    # Step 2: Try progressively shorter formats
    formats = [
        f"{away} {time_token} {home}",      # "LAR 3p CHI" (full)
        f"{away}{time_token}{home}",        # "LAR3pCHI" (no spaces)
        f"{away[:2]}@{home[:2]}",           # "LA@CH" (2-letter codes)
        f"{away[:2]}v{home[:2]}",           # "LAvCH" (shorter separator)
    ]

    chosen = formats[-1]  # Default to shortest
    for fmt in formats:
        if estimate_width(fmt) <= available:
            chosen = fmt
            break

    # Step 3: Build payload
    return {
        "name": "Matchup",
        "icon": 12345,
        "text": "",
        "noScroll": True,
        "duration": 5,
        "lifetime": 300,
        "draw": [
            {"dt": [icon_budget, 1, chosen, "#FFFFFF"]},
            {"df": [badge_x, 0, badge_width, 8, "#333333"]},
            {"dt": [badge_x + 1, 1, "B", "#FFFFFF"]},
        ],
    }
```

**Key insight:** The loop tries formats in order of preference (most readable first) and picks the
first one that fits. Separators (spaces, `@`, `v`) are progressively dropped.

### Layout debugging recipe

When your layout looks wrong, add this debugging block:

```python
def compile_with_debug(text: str, available: int) -> dict:
    width = estimate_width(text)
    margin = available - width

    # Print debug info (visible in --dry-run output)
    print(f"Layout debug:")
    print(f"  Text: '{text}'")
    print(f"  Computed width: {width}px")
    print(f"  Available: {available}px")
    print(f"  Margin: {margin}px {'✓' if margin >= 0 else '✗ OVERFLOW'}")

    if margin < 0:
        print(f"  Need to cut: {abs(margin)}px")

    # ... rest of payload
```

**Checklist for layout issues:**
- [ ] Print computed width for each text element
- [ ] Print available space after subtracting anchors
- [ ] Print final x position for each `dt` command
- [ ] Print remaining margin (should be >= 0)
- [ ] Test with worst-case strings (WMWMWMW, not IIIIIII)

### Quick reference: common widths

| String | Width | Breakdown |
|--------|-------|-----------|
| `"5.2¢"` | 13px | 5(3)+.(1)+2(3)+¢(3) + 3 gaps |
| `"Jan 14"` | 20px | J(3)+a(3)+n(3)+sp(1)+1(2)+4(3) + 5 gaps |
| `"3:45p"` | 17px | 3(3)+:(1)+4(3)+5(3)+p(3) + 4 gaps |
| `"LA"` | 7px | L(3)+A(3) + 1 gap |
| `"LAR"` | 11px | L(3)+A(3)+R(3) + 2 gaps |
| `"BEARS"` | 19px | B(3)+E(3)+A(3)+R(3)+S(3) + 4 gaps |
| `"MIAMI"` | 19px | M(5)+I(1)+A(3)+M(5)+I(1) + 4 gaps |
| `"WAS"` | 13px | W(5)+A(3)+S(3) + 2 gaps |

## Layout patterns gallery

These are known-good layout patterns used in this repo. Each pattern includes the visual structure
and key implementation notes.

### Pattern 1: Icon + text (simple)

```
┌────────────────────────────────┐
│[icon]  Text here               │
└────────────────────────────────┘
```

Used by: `comed_price_display.py`, `solar_display.py`

```python
{
    "icon": 12345,
    "text": "5.2¢",
    "noScroll": True,
}
```

Notes: Icon uses ~8px + 1px gap = 9px, leaving 23px for text. Budget pixels, not characters.

### Pattern 2: Right-side box

```
┌────────────────────────────────┐
│ Month Day        ┌────┐        │
│                  │ Tu │        │
│                  └────┘        │
└────────────────────────────────┘
```

Used by: `display_date.py`

```python
box_width = 9
box_x = 32 - box_width
{
    "text": "",
    "draw": [
        {"df": [box_x, 0, box_width, 8, box_color]},
        {"dt": [box_x + 1, 1, "Tu", "#FFFFFF"]},
        {"dt": [0, 1, "Jan 14", text_color]},
    ],
}
```

Notes: Anchor the box to the right edge first, then fill remaining space with left-aligned content.

### Pattern 3: Progress bar

```
┌────────────────────────────────┐
│[icon]  Value                   │
│████████░░░░░░░░░░░░░░░░░░░░░░░░│
└────────────────────────────────┘
```

Used by: `display_garmin_connect.py`

```python
{
    "icon": 12345,
    "text": "8,234",
    "progress": 75,        # 0-100
    "progressC": "#00FF00",
}
```

Notes: Progress bar renders at the bottom. Keep values in 0-100 range.

### Pattern 4: Compact matchup (sports)

```
┌────────────────────────────────┐
│[icon] LA 3p Ca           ┌───┐ │
│                          │ B │ │
│                          └───┘ │
└────────────────────────────────┘
```

Used by: `sports_schedule.py`

```python
# Matchup text with time token and right-side team marker
{
    "icon": league_icon,
    "text": "",
    "draw": [
        {"dt": [9, 1, "LA 3p Ca", urgency_color]},
        {"df": [box_x, 0, 7, 8, team_color]},
        {"dt": [box_x + 2, 1, "B", "#FFFFFF"]},
    ],
}
```

Notes: Use 2-letter location codes from `team.location` to save pixels. Time token (`3p`) or
weekday token (`Sa`) goes between teams.

## Icons

Shared icon IDs live in `awtrix3/icon_draw.py` as `icon_draw.awtrix_icons`.

- Prefer using existing IDs from `icon_draw.awtrix_icons` or the league icon mapping in
  `awtrix3/sports_teams.yaml`.
- If you add a new icon ID, keep the key descriptive and the mapping centralized in `icon_draw.py` unless it is
  truly league-specific (then add it to `sports_teams.yaml`).

## Colors and display limitations

### Color selection

LED matrix displays work best with high-contrast colors:

- Use bright colors (`#FFFFFF`, `#00FF00`, `#FF0000`) for text on dark backgrounds.
- Avoid dark text on dark backgrounds or light text on light backgrounds.
- Colors can be specified as `"#RRGGBB"` strings or `[r, g, b]` arrays.

### Display limitations

- **No Unicode/emoji support**: AWTRIX uses a built-in bitmap font. Stick to ASCII characters.
- **Limited resolution**: 32x8 pixels means text must be concise. Aim for 4-6 characters without scrolling.
- **Brightness**: Very dim colors may be invisible. Test on the actual device.

## Multi-app scripts

Some modules naturally produce multiple apps (for example one per configured entity).

The established pattern (used by `sports_schedule.py`) is:

- `compile_*_apps(...) -> list[dict] | None`
- `send_to_awtrix(app_data)` accepts a list and iterates, sending each payload.
- Each returned payload has a stable per-entity `name`, for example `${short_name}NextGame`.

## Configuration files in `awtrix3/`

These scripts expect small YAML config files in this folder.

- `awtrix3/api.yml`
  - Keys: `ip`, `username`, `password`
  - Used by scripts that send directly to the device.
  - Do not include real credentials in documentation examples.
- `awtrix3/sports_teams.yaml`
  - `league_icons`: mapping from league code to icon ID.
  - `teams`: list of entries with `enabled`, `league`, `short_name`, and league-specific settings.
  - `sports_schedule.py` supports a league-wide mode via `mode: league` and searches for the config in CWD
    first and then in the script directory.
- `awtrix3/garmin_login.yml`
  - Keys: `email`, `password`
  - Used by `display_garmin_connect.py`.

## Rate limiting and update cadence

Two different rate limits matter:

- External APIs: `sports_schedule.py` sleeps a small random amount before ESPN requests.
- AWTRIX device: `send_price.py` sleeps between POSTs to avoid hammering the display.

When adding a new app:

- Keep payloads small (especially `draw` lists).
- Use a `lifetime` that matches how often the app will be refreshed.
- Avoid sending many apps back-to-back without delay.

## Orchestration with `send_price.py`

`awtrix3/send_price.py` is a simple orchestrator that:

- Calls payload generators from multiple modules.
- Posts each payload to AWTRIX.
- Uses `GET /api/loop` to print the currently active app loop positions for debugging.

To add a new app to the loop, import your module and call your `compile_*()` function in `send_price.py`, then
pass its payload to `send_to_awtrix()`.

## Testing your app

### Local testing with dry-run

Always test with `--dry-run` first to inspect the payload without sending:

```bash
python3 my_app.py --dry-run
```

### Checking device state

Use the AWTRIX API to inspect the current loop and debug issues:

```bash
# Get current app loop
curl http://<ip>/api/loop

# Get device stats
curl http://<ip>/api/stats

# Delete an app from the loop
curl -X POST http://<ip>/api/custom?name=MyApp -d '{}'
```

### Iterating on layouts

For draw-heavy layouts, iterate quickly by:

1. Running with `--dry-run` to verify the payload structure.
2. Sending to the device and observing the result.
3. Adjusting coordinates and re-sending.

## Error handling

Scripts should handle common failure modes gracefully:

```python
def send_to_awtrix(app_data: dict) -> bool:
    try:
        response = requests.post(url, json=app_data, auth=auth, timeout=10)
        if response.status_code != 200:
            print(f"AWTRIX error: {response.status_code} - {response.text}")
            return False
        return True
    except requests.exceptions.ConnectionError:
        print(f"Cannot connect to AWTRIX at {config['ip']}")
        return False
    except requests.exceptions.Timeout:
        print("Request timed out")
        return False
```

For external API calls (ESPN, etc.), wrap in try/except and return `None` from `compile_*()` on failure.

## Troubleshooting

Quick reference for common display issues. For deeper problems (timezone drift, API failures, orphan
apps), see [AWTRIX3_PYTHON_SPEC.md#troubleshooting-and-gotchas](AWTRIX3_PYTHON_SPEC.md#troubleshooting-and-gotchas).

| Symptom | Likely cause | Solution |
|---------|--------------|----------|
| App not appearing | `lifetime` expired | Increase `lifetime` or run script more frequently |
| App not appearing | `stack: False` | Set `stack: True` to join the app loop |
| Text cut off | Text too wide | Shorten text or enable scrolling |
| Text scrolling unexpectedly | `noScroll` not set | Add `"noScroll": True` |
| Wrong colors | Color format issue | Use `"#RRGGBB"` or `[r, g, b]` consistently |
| 401 Unauthorized | Wrong credentials | Check `api.yml` username/password |
| Connection refused | Wrong IP or device offline | Verify IP in `api.yml`, check device power |
| App flickers | Sending too frequently | Add delay between sends, increase `lifetime` |
