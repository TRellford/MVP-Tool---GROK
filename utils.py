from nba_api.stats.endpoints import playergamelog, leaguegamefinder
from nba_api.stats.static import players
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- Constants ---
ODDS_API_KEY = '06f33a81a9869429c717a7ac27b205ae'
SPORT = "basketball_nba"
SEASON = "2024-25"

# --- Helper Functions ---

def get_player_id(player_name):
    """Find a player's ID by their full name."""
    player_dict = players.find_players_by_full_name(player_name)
    return player_dict[0]['id'] if player_dict else None

def fetch_game_logs(player_id):
    """Fetch a player's game logs for the season."""
    try:
        game_log = playergamelog.PlayerGameLog(player_id=player_id, season=SEASON)
        return game_log.get_data_frames()[0]
    except Exception as e:
        return None

def get_last_10_games(df):
    """Filter to the last 10 games from game logs."""
    if df is None or len(df) == 0:
        return None
    return df.head(10) if len(df) >= 10 else df

def calculate_averages(df):
    """Calculate average stats over the selected games."""
    if df is None:
        return None
    return {
        'Points': df['PTS'].mean(),
        'Rebounds': df['REB'].mean(),
        'Assists': df['AST'].mean(),
        'Minutes': df['MIN'].mean()
    }

def fetch_nba_games(today=True):
    """Fetch NBA games for today or tomorrow."""
    game_finder = leaguegamefinder.LeagueGameFinder(league_id_nullable='00', season_nullable=SEASON)
    games_df = game_finder.get_data_frames()[0]
    date_str = datetime.now().strftime("%Y-%m-%d") if today else (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    return games_df[games_df['GAME_DATE'] == date_str]['MATCHUP'].tolist()

def fetch_odds(game_matchup):
    """Fetch odds for a specific game from The Odds API."""
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/?apiKey={ODDS_API_KEY}®ions=us&markets=h2h,spreads,totals"
    response = requests.get(url)
    if response.status_code == 200:
        odds_data = response.json()
        for game in odds_data:
            if game_matchup in f"{game['home_team']} vs. {game['away_team']}" or game_matchup in f"{game['away_team']} @ {game['home_team']}":
                return game['bookmakers'][0]['markets']  # First bookmaker
    return None

def calculate_betting_edge(avg_stat, odds_line, odds_price):
    """Calculate expected value (EV) for a betting line."""
    if odds_price > 0:
        implied_prob = 100 / (odds_price + 100)
    else:
        implied_prob = -odds_price / (-odds_price + 100)
    hit_rate = 1 if avg_stat > odds_line else 0  # Simplified hit rate
    ev = (hit_rate * (odds_price / 100 if odds_price > 0 else 1)) - ((1 - hit_rate) * 1)
    return ev
