"""Load sports configuration and fetch upcoming events for the AWTRIX display."""

# Standard Library
import os
import time
import random
from datetime import datetime

# PIP3 modules
import yaml
import requests

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

