#!/usr/bin/env python3

"""
Sports countdown module for AWTRIX 3 display.
Fetches next game times from ESPN/Ergast APIs and displays countdown.
"""

# Standard Library
import os
import time
import random
import argparse
import math
from datetime import datetime

# PIP3 modules
import yaml
import colorsys
import requests

# Local repo modules
import icon_draw

#============================================
def ensure_min_brightness(hex_color: str, min_brightness: float = 0.5) -> str:
	"""
	Ensure a hex color has minimum brightness for visibility on dark backgrounds.

	Args:
		hex_color (str): Hex color string like "#0B162A".
		min_brightness (float): Minimum brightness value (0-1). Default 0.5.

	Returns:
		str: Adjusted hex color with minimum brightness.
	"""
	# Parse hex color
	hex_color = hex_color.lstrip("#")
	r = int(hex_color[0:2], 16) / 255.0
	g = int(hex_color[2:4], 16) / 255.0
	b = int(hex_color[4:6], 16) / 255.0

	# Convert to HSV
	h, s, v = colorsys.rgb_to_hsv(r, g, b)

	# Ensure minimum brightness (value)
	if v < min_brightness:
		v = min_brightness

	# Convert back to RGB
	r, g, b = colorsys.hsv_to_rgb(h, s, v)

	# Format as hex
	result = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
	return result

#============================================
def _hex_to_rgb01(hex_color: str) -> tuple:
	hex_color = (hex_color or "").strip().lstrip("#")
	if len(hex_color) != 6:
		return None
	r = int(hex_color[0:2], 16) / 255.0
	g = int(hex_color[2:4], 16) / 255.0
	b = int(hex_color[4:6], 16) / 255.0
	return (r, g, b)

#============================================
def _relative_luminance(hex_color: str) -> float:
	"""
	Compute relative luminance per WCAG (0=dark, 1=light).
	"""
	rgb = _hex_to_rgb01(hex_color)
	if rgb is None:
		return 0.0

	def _lin(c: float) -> float:
		return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

	r, g, b = rgb
	rl, gl, bl = _lin(r), _lin(g), _lin(b)
	return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl

#============================================
def choose_bg_and_text_colors(primary: str, alternate: str, debug: bool = False, label: str = "") -> tuple:
	"""
	Choose box background and text colors from two team colors.

	ESPN team colors are hex strings without a leading '#'.
	"""
	primary = (primary or "").strip()
	alternate = (alternate or "").strip()
	if primary and not primary.startswith("#"):
		primary = f"#{primary}"
	if alternate and not alternate.startswith("#"):
		alternate = f"#{alternate}"

	if not primary and not alternate:
		if debug:
			print(f"  colors[{label}]: missing primary+alternate -> bg=#333333 fg=#ffffff")
		return ("#333333", "#ffffff")

	if primary and not alternate:
		bg = primary
		fg = "#ffffff"
		if debug:
			print(f"  colors[{label}]: primary-only bg={bg} fg={fg}")
		return (bg, fg)

	if alternate and not primary:
		bg = alternate
		fg = "#000000" if _relative_luminance(bg) > 0.6 else "#ffffff"
		if debug:
			print(f"  colors[{label}]: alternate-only bg={bg} fg={fg}")
		return (bg, fg)

	lp = _relative_luminance(primary)
	la = _relative_luminance(alternate)

	def _contrast_ratio(bg_color: str, fg_color: str) -> float:
		lbg = _relative_luminance(bg_color)
		lfg = _relative_luminance(fg_color)
		l1 = max(lbg, lfg)
		l2 = min(lbg, lfg)
		return (l1 + 0.05) / (l2 + 0.05)

	def _best_text_for_bg(bg_color: str, preferred_fg: str) -> tuple:
		if preferred_fg:
			cr = _contrast_ratio(bg_color, preferred_fg)
			if cr >= 2.5:
				return (preferred_fg, cr)
		black_cr = _contrast_ratio(bg_color, "#000000")
		white_cr = _contrast_ratio(bg_color, "#ffffff")
		if black_cr >= white_cr:
			return ("#000000", black_cr)
		return ("#ffffff", white_cr)

	# Evaluate both orientations and pick the better one; break ties by preferring the brighter background.
	fg1, cr1 = _best_text_for_bg(primary, alternate)
	fg2, cr2 = _best_text_for_bg(alternate, primary)

	if cr2 > cr1 or (cr2 == cr1 and la > lp):
		bg = alternate
		fg = fg2
		cr = cr2
	else:
		bg = primary
		fg = fg1
		cr = cr1

	# If the chosen foreground is a "light" team color, ensure it is not too dim on AWTRIX.
	if _relative_luminance(fg) > _relative_luminance(bg):
		fg = ensure_min_brightness(fg, min_brightness=0.65)

	if debug:
		print(
			f"  colors[{label}]: primary={primary} (L={lp:.3f}) alt={alternate} (L={la:.3f})"
			f" -> bg={bg} fg={fg} (contrast={cr:.2f})"
		)

	return (bg, fg)

#============================================
# ESPN API endpoints by league
ESPN_LEAGUES = {
	"nfl": "football/nfl",
	"nba": "basketball/nba",
	"wnba": "basketball/wnba",
	"mlb": "baseball/mlb",
	"nhl": "hockey/nhl",
	"ncaaf": "football/college-football",
	"ncaab": "basketball/mens-college-basketball",
}

# Ergast F1 API base URL
ERGAST_BASE = "https://ergast.com/api/f1"

#============================================
def find_config_file(config_path: str = None) -> str:
	"""
	Find the config file, checking CWD first, then script directory.

	Args:
		config_path (str): Optional override path to config file.

	Returns:
		str: Path to config file.

	Raises:
		FileNotFoundError: If no config file found.
	"""
	config_name = "sports_teams.yaml"

	# If explicit path provided, use it directly
	if config_path is not None:
		if os.path.exists(config_path):
			return config_path
		raise FileNotFoundError(f"Config file not found: {config_path}")

	# Check current working directory first
	cwd_path = os.path.join(os.getcwd(), config_name)
	if os.path.exists(cwd_path):
		return cwd_path

	# Fall back to script directory
	script_dir = os.path.dirname(os.path.abspath(__file__))
	script_path = os.path.join(script_dir, config_name)
	if os.path.exists(script_path):
		return script_path

	raise FileNotFoundError(f"Config file '{config_name}' not found in CWD or script directory")

#============================================
def is_league_in_season(team_config: dict) -> bool:
	"""
	Check if a league is currently in season based on active_months config.

	Args:
		team_config (dict): Team configuration with optional active_months field.

	Returns:
		bool: True if league is in season or no active_months specified.
	"""
	active_months = team_config.get("active_months", None)

	# If no active_months specified, assume always in season
	if not active_months:
		return True

	current_month = datetime.now().month
	return current_month in active_months

#============================================
def load_teams_config(config_path: str = None) -> tuple:
	"""
	Load teams configuration from YAML file.

	Args:
		config_path (str): Path to YAML config file. Defaults to sports_teams.yaml.

	Returns:
		tuple: (list of team configs, dict of league icons)
	"""
	config_path = find_config_file(config_path)

	with open(config_path, "r") as f:
		config = yaml.safe_load(f)

	teams = config.get("teams", [])
	league_icons = config.get("league_icons", {})
	# Filter to enabled teams only
	enabled_teams = [t for t in teams if t.get("enabled", True)]
	return enabled_teams, league_icons

#============================================
def fetch_espn_next_game(league: str, team_id: str) -> dict:
	"""
	Fetch next game for a team from ESPN API.

	Args:
		league (str): League code (nfl, nba, mlb, nhl, wnba).
		team_id (str): ESPN team abbreviation (e.g., CHI).

	Returns:
		dict: Game info with 'datetime', 'opponent', 'home' keys, or None.
	"""
	if league not in ESPN_LEAGUES:
		print(f"Unknown ESPN league: {league}")
		return None

	sport_path = ESPN_LEAGUES[league]
	url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}/schedule"

	# Add delay to avoid overloading server
	time.sleep(random.random())

	response = requests.get(url, timeout=10)
	if response.status_code != 200:
		print(f"ESPN API error {response.status_code} for {team_id} in {league}")
		return None

	data = response.json()
	events = data.get("events", [])

	# Find the next upcoming game
	for event in events:
		game_date_str = event.get("date", "")
		if not game_date_str:
			continue

		# Parse ISO format datetime (ESPN uses UTC with Z suffix)
		game_date_str = game_date_str.replace("Z", "+00:00")
		game_dt = datetime.fromisoformat(game_date_str)
		# Store local time for display (naive datetime)
		game_dt_local = game_dt.replace(tzinfo=None)

		# Get opponent info
		competitions = event.get("competitions", [{}])
		if competitions:
			competitors = competitions[0].get("competitors", [])
			opponent = "TBD"
			is_home = False
			for comp in competitors:
				comp_abbrev = comp.get("team", {}).get("abbreviation", "")
				if comp_abbrev.upper() != team_id.upper():
					opponent = comp.get("team", {}).get("displayName", "TBD")
				else:
					is_home = comp.get("homeAway", "") == "home"

		# Check if game is in the future (compare UTC times)
		# ESPN returns UTC, so compare with UTC now
		from datetime import timezone
		now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
		game_dt_utc = game_dt.replace(tzinfo=None)

		if game_dt_utc > now_utc:
			result = {
				"datetime": game_dt,
				"datetime_local": game_dt_local,
				"opponent": opponent,
				"home": is_home,
				"event_name": event.get("name", ""),
			}
			return result

	# No upcoming games found (off-season or end of schedule)
	return None

#============================================
def fetch_espn_next_league_event(league: str) -> dict:
	"""
	Fetch the next upcoming event for an ESPN league.

	Args:
		league (str): League code (nfl, nba, mlb, nhl, wnba, ...).

	Returns:
		dict: Event info with 'datetime' and 'opponent' (matchup) keys, or None.
	"""
	if league not in ESPN_LEAGUES:
		print(f"Unknown ESPN league: {league}")
		return None

	sport_path = ESPN_LEAGUES[league]
	url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard"

	time.sleep(random.random())

	response = requests.get(url, timeout=10)
	if response.status_code != 200:
		print(f"ESPN API error {response.status_code} for league {league}")
		return None

	data = response.json()
	events = data.get("events", [])

	from datetime import timezone
	now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

	for event in events:
		event_date_str = event.get("date", "")
		if not event_date_str:
			continue

		event_date_str = event_date_str.replace("Z", "+00:00")
		event_dt = datetime.fromisoformat(event_date_str)

		event_dt_utc = event_dt.replace(tzinfo=None)
		if event_dt_utc <= now_utc:
			continue

		# Build a compact matchup string like "GB@CHI" when possible.
		matchup = event.get("name", "TBD")
		competitions = event.get("competitions", [])
		home_team = None
		away_team = None
		if competitions:
			competitors = competitions[0].get("competitors", [])
			home = None
			away = None
			for comp in competitors:
				team = comp.get("team", {})
				abbr = team.get("abbreviation", None)
				if abbr is None:
					continue
				if comp.get("homeAway", "") == "home":
					home = abbr
					home_team = {
						"abbreviation": abbr,
						"location": team.get("location", ""),
						"color": team.get("color", None),
						"alternateColor": team.get("alternateColor", None),
					}
				elif comp.get("homeAway", "") == "away":
					away = abbr
					away_team = {
						"abbreviation": abbr,
						"location": team.get("location", ""),
						"color": team.get("color", None),
						"alternateColor": team.get("alternateColor", None),
					}
			if home and away:
				matchup = f"{away}@{home}"

		result = {
			"datetime": event_dt,
			"datetime_local": event_dt.replace(tzinfo=None),
			"opponent": matchup,
			"home_team": home_team,
			"away_team": away_team,
			"home": None,
			"event_name": event.get("name", ""),
		}
		return result

	return None

#============================================
def fetch_f1_next_race() -> dict:
	"""
	Fetch next F1 race from Ergast API.

	Returns:
		dict: Race info with 'datetime', 'name', 'circuit' keys, or None.
	"""
	url = f"{ERGAST_BASE}/current.json"

	time.sleep(random.random())

	response = requests.get(url, timeout=10)
	if response.status_code != 200:
		print(f"Ergast API error {response.status_code}")
		return None

	data = response.json()
	races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])

	now = datetime.now()

	for race in races:
		race_date = race.get("date", "")
		race_time = race.get("time", "14:00:00Z")  # Default time if missing
		race_time = race_time.replace("Z", "")

		datetime_str = f"{race_date}T{race_time}"
		race_dt = datetime.fromisoformat(datetime_str)

		if race_dt > now:
			result = {
				"datetime": race_dt,
				"name": race.get("raceName", "Race"),
				"circuit": race.get("Circuit", {}).get("circuitName", ""),
			}
			return result

	return None

#============================================
def fetch_next_game(team_config: dict) -> dict:
	"""
	Fetch next game for a team based on its league.

	Args:
		team_config (dict): Team configuration from YAML.

	Returns:
		dict: Game info or None if no upcoming game.
	"""
	league = team_config.get("league", "").lower()
	team_id = team_config.get("espn_team_id", "")
	mode = team_config.get("mode", "team").lower()

	if league == "f1":
		game = fetch_f1_next_race()
	elif mode == "league" and league in ESPN_LEAGUES:
		game = fetch_espn_next_league_event(league)
	elif league in ESPN_LEAGUES:
		game = fetch_espn_next_game(league, team_id)
	else:
		print(f"Unsupported league: {league}")
		return None

	if game:
		# Attach team config to the game info
		game["team_config"] = team_config

	return game

#============================================
def format_countdown(target_dt: datetime) -> str:
	"""
	Format time remaining as a readable countdown string.

	Args:
		target_dt (datetime): Target datetime (UTC).

	Returns:
		str: Formatted countdown like "8h 12m" or "2d 5h".
	"""
	from datetime import timezone
	now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
	target_utc = target_dt.replace(tzinfo=None)

	delta = target_utc - now_utc
	total_seconds = int(delta.total_seconds())

	if total_seconds < 0:
		return "LIVE"

	days = total_seconds // 86400
	hours = (total_seconds % 86400) // 3600
	minutes = (total_seconds % 3600) // 60

	# Round minutes to nearest 5 (matches 300s lifetime)
	minutes = (minutes // 5) * 5

	if days > 0:
		countdown_str = f"{days}d{hours}h"
	elif hours > 0:
		countdown_str = f"{hours}h{minutes:02d}"
	else:
		countdown_str = f"{minutes}m"

	return countdown_str

#============================================
def get_countdown_color(target_dt: datetime) -> list:
	"""
	Get color based on time remaining (green -> yellow -> orange -> red).

	Args:
		target_dt (datetime): Target datetime.

	Returns:
		list: RGB color as [r, g, b].
	"""
	from datetime import timezone
	now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
	target_utc = target_dt.replace(tzinfo=None)

	delta = target_utc - now_utc
	hours_remaining = delta.total_seconds() / 3600

	if hours_remaining > 24:
		# Green for more than a day away
		return [0, 255, 100]
	elif hours_remaining > 6:
		# Yellow-green
		return [180, 255, 0]
	elif hours_remaining > 2:
		# Orange
		return [255, 165, 0]
	else:
		# Red for imminent
		return [255, 50, 50]

#============================================
def compile_sports_countdown_apps(config_path: str = None, debug: bool = False) -> list:
	"""
	Compile countdown data for each enabled team/league entry.

	Args:
		config_path (str): Path to sports_teams.yaml config.

	Returns:
		list: List of AWTRIX display payload dictionaries.
	"""
	teams, league_icons = load_teams_config(config_path)

	if not teams:
		print("No enabled teams found in config")
		return None

	app_payloads = []

	for team in teams:
		team_name = team.get("name", "Unknown")

		# Skip teams whose league is not in season
		if not is_league_in_season(team):
			print(f"Skipping {team_name} (off-season)")
			continue

		print(f"Checking {team_name}...")
		next_game = fetch_next_game(team)
		if not next_game:
			print("  No upcoming games")
			continue

		team_config = next_game["team_config"]
		short_name = team_config.get("short_name", team_name.split()[-1][:4].upper())
		league = team_config.get("league", "").lower()
		mode = team_config.get("mode", "team").lower()
		show_matchup = bool(team_config.get("show_matchup", False))
		colors = team_config.get("colors", ["#FFFFFF", "#FFFFFF"])

		# Unique AWTRIX app name per team/entry (e.g., "BEARCountdown")
		app_name = f"{short_name}Countdown"

		# Format countdown
		countdown_str = format_countdown(next_game["datetime"])

		# Get league icon
		league_icon = league_icons.get(league, icon_draw.awtrix_icons.get("running man", 22835))

		# Check if entry uses letter-in-box display
		letter = team_config.get("letter", None)

		# Calculate box width based on letter width (M,W are 5px, I is 1px, others 3px)
		def _char_width(ch: str) -> int:
			if ch in {"M", "W", "m", "w"}:
				return 5
			if ch == "I":
				return 1  # AWTRIX 'I' is a single vertical line
			return 3

		# Layout: [Icon 8px] [Text] [Box on right]
		# Box width = 2px margin + letter + 2px margin
		letter_width = _char_width(letter) if letter else 3
		BOX_WIDTH = 2 + letter_width + 2  # 7 for most, 9 for M/W
		BOX_X = 32 - BOX_WIDTH  # Box on right side

		# Get entry colors
		box_color = team_config.get("box_color", colors[1] if len(colors) > 1 else "#FFFFFF")
		letter_color = team_config.get("letter_color", colors[0] if colors else "#000000")
		text_color = team_config.get("text_color", box_color)

		# For league mode, optionally compress matchup + countdown into a single-line string.
		def _location_to_code(location: str) -> str:
			parts = [p for p in location.replace("-", " ").split(" ") if p]
			if len(parts) >= 2:
				return (parts[0][0] + parts[1][0]).upper()
			if len(parts) == 1:
				return parts[0][:2].upper()
			return ""

		def _countdown_token(target_dt: datetime) -> str:
			from datetime import timezone
			now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
			target_utc = target_dt.replace(tzinfo=None)
			total_seconds = (target_utc - now_utc).total_seconds()
			if total_seconds < 0:
				return "0H"

			hours = total_seconds / 3600.0
			if hours >= 24:
				days = int(math.ceil(hours / 24.0))
				if debug:
					print(f"  countdown: hours={hours:.3f} -> days={days} (ceiling)")
				return f"{max(0, days)}d"
			# Avoid "0H" when < 1 hour remains; minutes are intentionally not shown.
			hours_int = int(math.ceil(hours))
			if debug:
				print(f"  countdown: seconds={total_seconds:.0f} hours={hours:.3f} -> {hours_int}H (ceiling)")
			return f"{max(0, hours_int)}H"

		def _nfl_countdown_token(target_dt: datetime) -> str:
			"""
			NFL-specific countdown/time format.
			<24 hours: show game time like "I2p" or "3a" (uses 'I' for narrow '1')
			4+ days: show days like "9d"
			Otherwise: show hours like "36'"
			"""
			from datetime import timezone
			now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
			target_utc = target_dt.replace(tzinfo=None)
			total_seconds = (target_utc - now_utc).total_seconds()
			if total_seconds < 0:
				return "now"

			total_hours = total_seconds / 3600.0
			total_days = total_seconds / 86400.0

			# <24 hours: show game time (e.g., "I2p", "3a")
			# Use 'I' instead of '1' for narrow display (AWTRIX 'I' is 1px wide)
			if total_hours < 24:
				# Convert to local time for display
				local_dt = target_dt.astimezone()
				hour = local_dt.hour
				if hour == 0:
					time_str = "I2a"  # 12am
				elif hour < 10:
					time_str = f"{hour}a"
				elif hour == 10:
					time_str = "IOa"  # 10am - use 'I' for 1, 'O' for 0
				elif hour == 11:
					time_str = "IIa"  # 11am
				elif hour == 12:
					time_str = "I2p"  # 12pm
				elif hour < 22:
					time_str = f"{hour - 12}p"
				elif hour == 22:
					time_str = "IOp"  # 10pm
				else:
					time_str = "IIp"  # 11pm
				if debug:
					print(f"  nfl_countdown: {total_seconds:.0f}s -> {time_str} (game time)")
				return time_str

			# 4+ days: show days
			if total_days >= 4:
				days = int(math.ceil(total_days))
				days = min(days, 99)  # cap at 99
				if debug:
					print(f"  nfl_countdown: {total_seconds:.0f}s -> {days}d")
				return f"{days}d"

			# Otherwise: show hours with '
			hours = int(math.ceil(total_hours))
			hours = min(hours, 99)  # cap at 99
			if debug:
				print(f"  nfl_countdown: {total_seconds:.0f}s -> {hours}'")
			return f"{hours}'"

		def _draw_team_abbr(x: int, y: int, text: str, color) -> list:
			"""
			Draw team abbreviation with serifed I when there's room.
			Uses serifed I (3px) if text has no M/W, otherwise narrow I (1px).
			"""
			has_wide = any(ch in text for ch in "MWmw")
			cmds = []
			cur_x = x
			for ch in text:
				# Use serifed I if no wide letters in abbreviation
				if ch == "I" and not has_wide:
					# Draw 3px wide serifed I: top serif, stem, bottom serif
					cmds.append({"dl": [cur_x, y, cur_x + 2, y, color]})        # top serif
					cmds.append({"dl": [cur_x + 1, y + 1, cur_x + 1, y + 3, color]})  # stem
					cmds.append({"dl": [cur_x, y + 4, cur_x + 2, y + 4, color]})  # bottom serif
					cur_x += 3 + 1  # 3px char + 1px kerning
				else:
					cmds.append({"dt": [cur_x, y, ch, color]})
					cur_x += _char_width(ch) + 1
			return cmds

		def _team_abbr_width(text: str) -> int:
			"""Calculate width of team abbreviation with serifed I logic."""
			has_wide = any(ch in text for ch in "MWmw")
			width = 0
			for i, ch in enumerate(text):
				if ch == "I" and not has_wide:
					width += 3  # serifed I
				else:
					width += _char_width(ch)
				if i < len(text) - 1:
					width += 1  # kerning
			return width

		def _build_nfl_layout(away_team: dict, home_team: dict, target_dt: datetime) -> tuple:
			"""
			Build fixed-width NFL layout: 9 columns per team box, 14 columns for time.
			Always uses 2-letter abbreviations.
			Layout: [Away 9px] [Time 14px] [Home 9px] = 32px total
			"""
			# Get 2-letter abbreviations (first 2 chars of ESPN abbreviation)
			away_abbr = (away_team.get("abbreviation", "") or "")[:2].upper()
			home_abbr = (home_team.get("abbreviation", "") or "")[:2].upper()

			# Use NFL countdown format with ' and "
			token = _nfl_countdown_token(target_dt)
			token_w = _text_width(token)

			# Fixed box dimensions
			BOX_W = 9
			BOX_H = 7
			TIME_W = 14  # 32 - 9 - 9 = 14

			# Calculate text widths for centering within boxes (using serifed I logic)
			away_text_w = _team_abbr_width(away_abbr)
			home_text_w = _team_abbr_width(home_abbr)

			# Box positions
			away_box_x = 0
			time_x = BOX_W
			home_box_x = BOX_W + TIME_W

			# Center text within boxes (box is 9px, text varies)
			away_text_x = away_box_x + (BOX_W - away_text_w) // 2
			home_text_x = home_box_x + (BOX_W - home_text_w) // 2

			# Center time in middle area (round up for slight right bias when odd)
			time_text_x = time_x + (TIME_W - token_w + 1) // 2

			# NFL team colors: prefer primary as background unless too dark
			MIN_RGB_SUM = 128  # threshold for "too dark" background (R+G+B)
			def _rgb_sum(hex_color: str) -> int:
				"""Sum of RGB values (0-765)."""
				hex_color = (hex_color or "").strip().lstrip("#")
				if len(hex_color) != 6:
					return 0
				r = int(hex_color[0:2], 16)
				g = int(hex_color[2:4], 16)
				b = int(hex_color[4:6], 16)
				return r + g + b

			def _nfl_team_colors(team: dict, label: str) -> tuple:
				"""Use primary ESPN color as bg, alternate as text (swap if primary too dark)."""
				primary = (team.get("color", "") or "").strip()
				alternate = (team.get("alternateColor", "") or "").strip()
				if primary and not primary.startswith("#"):
					primary = f"#{primary}"
				if alternate and not alternate.startswith("#"):
					alternate = f"#{alternate}"

				# Fallback if missing colors
				if not primary and not alternate:
					return ("#333333", "#ffffff")
				if not primary:
					primary = alternate
				if not alternate:
					alternate = primary

				rgb_primary = _rgb_sum(primary)
				rgb_alternate = _rgb_sum(alternate)

				# Use primary as background unless it's too dark
				if rgb_primary >= MIN_RGB_SUM:
					bg = primary
					fg = alternate
				else:
					bg = alternate
					fg = primary

				# Ensure text color has minimum brightness for visibility
				fg = ensure_min_brightness(fg, min_brightness=0.5)

				if debug:
					print(f"  nfl_colors[{label}]: primary={primary}(rgb={rgb_primary}) alt={alternate}(rgb={rgb_alternate}) -> bg={bg} fg={fg}")
				return (bg, fg)

			away_bg, away_fg = _nfl_team_colors(away_team, f"away:{away_abbr}")
			home_bg, home_fg = _nfl_team_colors(home_team, f"home:{home_abbr}")

			# Time color based on urgency
			time_color = get_countdown_color(target_dt)

			# Build draw commands
			draw = [
				# Away team box (left)
				{"df": [away_box_x, 0, BOX_W, BOX_H, away_bg]},
				# Home team box (right)
				{"df": [home_box_x, 0, BOX_W, BOX_H, home_bg]},
				# Time in center (uses 'I' for narrow '1' - AWTRIX 'I' is 1px wide)
				{"dt": [time_text_x, 1, token, time_color]},
			]
			# Add team abbreviations with serifed I where appropriate
			draw.extend(_draw_team_abbr(away_text_x, 1, away_abbr, away_fg))
			draw.extend(_draw_team_abbr(home_text_x, 1, home_abbr, home_fg))

			meta = {
				"away_text": away_abbr,
				"home_text": home_abbr,
				"token": token,
				"layout": "nfl_fixed",
				"away_box_x": away_box_x,
				"time_x": time_text_x,
				"home_box_x": home_box_x,
			}

			if debug:
				print(f"  nfl_layout: away={away_abbr}({away_text_w}px) time={token}({token_w}px) home={home_abbr}({home_text_w}px)")
				print(f"  nfl_layout: positions away_text={away_text_x} time={time_text_x} home_text={home_text_x}")

			return (draw, meta)

		# Helper function for text width calculation (used by both NFL and generic layouts)
		def _text_width(text: str) -> int:
			if not text:
				return 0
			width = 0
			for i, ch in enumerate(text):
				width += _char_width(ch)
				if i < len(text) - 1:
					width += 1
			return width

		matchup_text = countdown_str
		use_icon = True
		draw_commands = []
		payload_color = text_color

		if mode == "league" and show_matchup:
			away_team = next_game.get("away_team", None) or {}
			home_team = next_game.get("home_team", None) or {}
			away_loc = away_team.get("location", "")
			home_loc = home_team.get("location", "")
			away_loc2 = _location_to_code(away_loc)
			home_loc2 = _location_to_code(home_loc)
			away_abbr = (away_team.get("abbreviation", "") or "").upper()
			home_abbr = (home_team.get("abbreviation", "") or "").upper()

			# In league matchup mode, draw the layout explicitly:
			# This keeps the entire display single-line and avoids icons.
			use_icon = False
			payload_color = get_countdown_color(next_game["datetime"])

			# Football leagues use fixed-width layout: 9+14+9 columns with 2-letter abbreviations
			if league in ("nfl", "ncaaf"):
				draw_commands, draw_meta = _build_nfl_layout(away_team, home_team, next_game["datetime"])
				matchup_text = ""
				if debug:
					print(f"  league debug ({league.upper()} fixed layout):")
					print(f"    away_team: {away_team}")
					print(f"    home_team: {home_team}")
					if draw_meta is not None:
						print(f"    draw_meta: {draw_meta}")
			else:
				# Non-NFL leagues use the generic variable-width layout
				token = _countdown_token(next_game["datetime"])

				def _build_boxed_layout(away_text: str, home_text: str) -> tuple:
					away_w = _text_width(away_text)
					home_w = _text_width(home_text)
					token_w = _text_width(token)

					away_bg, away_fg = choose_bg_and_text_colors(
						away_team.get("color", None),
						away_team.get("alternateColor", None),
						debug=debug,
						label=f"away:{away_text}",
					)
					home_bg, home_fg = choose_bg_and_text_colors(
						home_team.get("color", None),
						home_team.get("alternateColor", None),
						debug=debug,
						label=f"home:{home_text}",
					)

					# Try tighter settings first if needed; prefer visible padding when possible.
					try_params = [
						(1, 2),
						(1, 1),
						(0, 1),
						(0, 0),
					]

					for padding_x, gap in try_params:
						away_box_w = away_w + (padding_x * 2)
						home_box_w = home_w + (padding_x * 2)
						total = away_box_w + gap + token_w + gap + home_box_w
						if total > 32:
							continue

						away_box_x = 0
						token_x = away_box_x + away_box_w + gap
						home_box_x = token_x + token_w + gap
						if home_box_x + home_box_w > 32:
							continue

						box_h = 7
						meta = {
							"away_text": away_text,
							"home_text": home_text,
							"token": token,
							"padding_x": padding_x,
							"gap": gap,
							"total_width": total,
							"away_box_w": away_box_w,
							"home_box_w": home_box_w,
							"token_w": token_w,
							"away_box_x": away_box_x,
							"token_x": token_x,
							"home_box_x": home_box_x,
						}
						return ([
							{"df": [away_box_x, 0, away_box_w, box_h, away_bg]},
							{"dt": [away_box_x + padding_x, 1, away_text, away_fg]},
							{"dt": [token_x, 1, token, payload_color]},
							{"df": [home_box_x, 0, home_box_w, box_h, home_bg]},
							{"dt": [home_box_x + padding_x, 1, home_text, home_fg]},
						], meta)

					return (None, None)

				# Prefer team abbreviations (3 letters), then fall back to compact location codes (2 letters).
				away_candidates = []
				home_candidates = []
				if away_abbr:
					away_candidates.append(away_abbr)
					away_candidates.append(away_abbr[:2])
				if away_loc2:
					away_candidates.append(away_loc2)
				if home_abbr:
					home_candidates.append(home_abbr.title())
					home_candidates.append(home_abbr[:2].title())
				if home_loc2:
					home_candidates.append(home_loc2.title())

				draw_commands = None
				draw_meta = None
				for away_text in away_candidates:
					for home_text in home_candidates:
						draw_commands, draw_meta = _build_boxed_layout(away_text, home_text)
						if draw_commands is not None:
							break
					if draw_commands is not None:
						break

				if draw_commands is not None and draw_meta is not None:
					matchup_text = ""
				else:
					# Fallback: show a compact matchup string with urgency coloring.
					matchup_text = next_game.get("opponent", "TBD")
					draw_commands = []

				if debug:
					print("  league debug:")
					print(f"    away_team: {away_team}")
					print(f"    home_team: {home_team}")
					print(f"    chosen_token: {token}")
					print(f"    away_candidates: {away_candidates}")
					print(f"    home_candidates: {home_candidates}")
					if draw_meta is not None:
						print(f"    draw_meta: {draw_meta}")
					else:
						print("    draw_meta: none (fell back to plain text)")

		if letter and mode != "league":
			# Team box on right side (7 rows, leave bottom row black)
			box_draw = {"df": [BOX_X, 0, BOX_WIDTH, 7, box_color]}
			draw_commands.append(box_draw)
			# Team letter (small font dt works, centered in box)
			letter_draw = {"dt": [BOX_X + 2, 1, letter, letter_color]}
			draw_commands.append(letter_draw)

		# AWTRIX payload
		data = {
			"name": app_name,
			"text": matchup_text,
			"color": payload_color,
			"textCase": 2,  # Preserve lowercase
			"repeat": 20,
			"center": False,
			"duration": 10,
			"stack": True,
			"lifetime": 300,
			"noScroll": True,
		}
		if use_icon:
			data["icon"] = league_icon
		if draw_commands:
			data["draw"] = draw_commands

		print(f"  Next: {next_game.get('opponent', next_game.get('name', 'TBD'))} ({countdown_str})")
		app_payloads.append(data)

	if not app_payloads:
		print("No upcoming games found for any enabled team")
		return None

	return app_payloads

#============================================
def compile_sports_countdown_data(config_path: str = None) -> dict:
	"""
	Backward compatible API: return the first compiled app payload (if any).
	"""
	apps = compile_sports_countdown_apps(config_path)
	if not apps:
		return None
	return apps[0]

#============================================
def get_api_config() -> dict:
	"""
	Load AWTRIX API configuration from api.yml.

	Returns:
		dict: Config with 'ip', 'username', 'password' keys.
	"""
	config_path = os.path.join(os.path.dirname(__file__), "api.yml")
	with open(config_path, "r") as f:
		config = yaml.safe_load(f)
	return config

#============================================
def send_to_awtrix(app_data) -> bool:
	"""
	Send data to AWTRIX 3 display.

	Args:
		app_data: AWTRIX payload dictionary, or a list of payload dictionaries.

	Returns:
		bool: True if successful, False otherwise.
	"""
	if app_data is None:
		print("No data to send")
		return False

	from requests.auth import HTTPBasicAuth

	config = get_api_config()
	ip = config["ip"]
	username = config["username"]
	password = config["password"]

	if isinstance(app_data, list):
		all_ok = True
		for one_app in app_data:
			ok = send_to_awtrix(one_app)
			all_ok = all_ok and ok
		return all_ok

	app_name = app_data.get("name", "SportsCountdown")
	url = f"http://{ip}/api/custom?name={app_name}"

	print(f"Sending to AWTRIX at {ip}...")
	response = requests.post(url, json=app_data, auth=HTTPBasicAuth(username, password))

	if response.status_code == 200:
		print(f"  Sent successfully: {app_data.get('text', '')}")
		return True
	else:
		print(f"  Failed: {response.status_code} {response.text}")
		return False

#============================================
def parse_args() -> argparse.Namespace:
	"""
	Parse command-line arguments.

	Returns:
		argparse.Namespace: Parsed arguments.
	"""
	parser = argparse.ArgumentParser(
		description="Sports countdown display for AWTRIX 3"
	)
	parser.add_argument(
		"-c", "--config", dest="config_path", type=str, default=None,
		help="Path to sports_teams.yaml config file"
	)
	parser.add_argument(
		"-d", "--dry-run", dest="dry_run", action="store_true",
		help="Do not send, just print data"
	)
	parser.add_argument(
		"--debug", dest="debug", action="store_true",
		help="Verbose output for layout, colors, and ESPN data"
	)
	parser.set_defaults(dry_run=False)
	parser.set_defaults(debug=False)
	args = parser.parse_args()
	return args

#============================================
def main():
	"""
	Main function to fetch sports countdown and display AWTRIX data.
	"""
	args = parse_args()
	data = compile_sports_countdown_apps(args.config_path, debug=args.debug)
	if data:
		print(f"\nAWTRIX Data: {data}")
		if not args.dry_run:
			send_to_awtrix(data)

#============================================
if __name__ == "__main__":
	main()
