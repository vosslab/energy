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

	if league == "f1":
		game = fetch_f1_next_race()
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
def compile_sports_countdown_data(config_path: str = None) -> dict:
	"""
	Compile countdown data for the next upcoming game across all enabled teams.

	Args:
		config_path (str): Path to teams YAML config.

	Returns:
		dict: AWTRIX display data dictionary.
	"""
	teams, league_icons = load_teams_config(config_path)

	if not teams:
		print("No enabled teams found in config")
		return None

	# Fetch next game for each enabled team
	upcoming_games = []
	for team in teams:
		team_name = team.get("name", "Unknown")

		# Skip teams whose league is not in season
		if not is_league_in_season(team):
			print(f"Skipping {team_name} (off-season)")
			continue

		print(f"Checking {team_name}...")
		game = fetch_next_game(team)
		if game:
			upcoming_games.append(game)
			print(f"  Next game: {game.get('opponent', game.get('name', 'TBD'))}")
		else:
			print("  No upcoming games")

	if not upcoming_games:
		print("No upcoming games found for any enabled team")
		return None

	# Sort by datetime to find the soonest game
	upcoming_games.sort(key=lambda g: g["datetime"])
	next_game = upcoming_games[0]

	# Extract display info
	team_config = next_game["team_config"]
	team_name = team_config.get("name", "Team")
	short_name = team_config.get("short_name", team_name.split()[-1][:4].upper())
	league = team_config.get("league", "").lower()
	colors = team_config.get("colors", ["#FFFFFF", "#FFFFFF"])

	# Unique AWTRIX app name per team (e.g., "BEARCountdown")
	app_name = f"{short_name}Countdown"

	# Format countdown
	countdown_str = format_countdown(next_game["datetime"])

	# Get league icon
	league_icon = league_icons.get(league, icon_draw.awtrix_icons.get("running man", 22835))

	# Check if team uses letter-in-box display
	letter = team_config.get("letter", None)

	# Calculate box width based on letter width (M,W are 5px, others 3px)
	def _char_width(ch: str) -> int:
		if ch in {"M", "W", "m", "w"}:
			return 5
		return 3

	# Layout: [Icon 8px] [Text] [Box on right]
	# Box width = 2px margin + letter + 2px margin
	letter_width = _char_width(letter) if letter else 3
	BOX_WIDTH = 2 + letter_width + 2  # 7 for most, 9 for M/W
	BOX_X = 32 - BOX_WIDTH  # Box on right side

	# Get team colors
	box_color = team_config.get("box_color", colors[1] if len(colors) > 1 else "#FFFFFF")
	letter_color = team_config.get("letter_color", colors[0] if colors else "#000000")
	text_color = team_config.get("text_color", box_color)

	# Note: letter_color should contrast with box_color (configured in YAML)

	# Build draw commands for box on right side
	draw_commands = []

	if letter:
		# Team box on right side (7 rows, leave bottom row black)
		box_draw = {"df": [BOX_X, 0, BOX_WIDTH, 7, box_color]}
		draw_commands.append(box_draw)
		# Team letter (small font dt works, centered in box)
		letter_draw = {"dt": [BOX_X + 2, 1, letter, letter_color]}
		draw_commands.append(letter_draw)

	# AWTRIX payload: icon on left, text after icon, draw box on right
	data = {
		"name": app_name,
		"text": countdown_str,
		"icon": league_icon,
		"color": text_color,
		"textCase": 2,  # Preserve lowercase
		"repeat": 20,
		"center": False,
		"duration": 10,
		"stack": True,
		"lifetime": 300,
		"noScroll": True,
		"draw": draw_commands,
	}

	# Add game info to output for debugging
	print(f"\nNext game: {team_name}")
	print(f"  vs {next_game.get('opponent', next_game.get('name', 'TBD'))}")
	print(f"  {next_game['datetime']}")
	print(f"  Countdown: {countdown_str}")

	return data

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
def send_to_awtrix(app_data: dict) -> bool:
	"""
	Send data to AWTRIX 3 display.

	Args:
		app_data (dict): AWTRIX payload dictionary.

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
	parser.set_defaults(dry_run=False)
	args = parser.parse_args()
	return args

#============================================
def main():
	"""
	Main function to fetch sports countdown and display AWTRIX data.
	"""
	args = parse_args()
	data = compile_sports_countdown_data(args.config_path)
	if data:
		print(f"\nAWTRIX Data: {data}")
		if not args.dry_run:
			send_to_awtrix(data)

#============================================
if __name__ == "__main__":
	main()
