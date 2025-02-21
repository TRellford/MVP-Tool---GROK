import streamlit as st
import requests
from scipy.stats import norm
from datetime import datetime
import json

# Access API key from Streamlit secrets
API_KEY = st.secrets.get("api_key")
if not API_KEY:
    raise ValueError("API key not set")

BASE_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba"
BALL_DONT_LIE_BASE_URL = "https://www.balldontlie.io/api/v1"

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_games_by_date(date_str):

    """
    Fetch NBA games for a specific date from The Odds API.
    
    Args:
        date_str (str): Date in YYYY-MM-DD format.
    
    Returns:
        list: List of games with relevant details.
    """
    url = f"{BASE_URL}/odds?apiKey={API_KEY}&regions=us&markets=h2h,spreads,totals&oddsFormat=american&date={date_str}T00:00:00Z"
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()
        return [
            {
                'id': game['id'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'commence_time': game['commence_time'],
                'bookmakers': game['bookmakers']
            } for game in games
        ]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching games: {e}")
        return []

@st.cache(ttl=3600)  # Cache for 1 hour
def find_player_games(player_name):
    """
    Find upcoming games for a player based on team schedules from The Odds API.
    
    Args:
        player_name (str): Name of the player.
    
    Returns:
        list: List of games involving the player's team.
    """
    url = f"{BASE_URL}/odds?apiKey={API_KEY}&regions=us&markets=h2h&oddsFormat=american"
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()
        player_games = []
        for game in games:
            if player_name.split()[-1] in game['home_team'] or player_name.split()[-1] in game['away_team']:
                player_games.append({
                    'id': game['id'],
                    'home_team': game['home_team'],
                    'away_team': game['away_team'],
                    'commence_time': game['commence_time'],
                    'bookmakers': game['bookmakers']
                })
        return player_games
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player games: {e}")
        return []

def is_player_in_game(player_name, game):
    """
    Check if a player is likely in a game (simplified check based on team names).
    
    Args:
        player_name (str): Name of the player.
        game (dict): Game information.
    
    Returns:
        bool: True if player is likely in the game, False otherwise.
    """
    return player_name.split()[-1] in game['home_team'] or player_name.split()[-1] in game['away_team']

@st.cache(ttl=3600)  # Cache for 1 hour
def get_player_prop_odds(game_id, prop):
    """
    Fetch player prop odds from The Odds API.
    
    Args:
        game_id (str): Unique identifier for the game.
        prop (str): Prop type (e.g., player_points).
    
    Returns:
        list or None: Prop odds outcomes if available, None otherwise.
    """
    url = f"{BASE_URL}/events/{game_id}/odds?apiKey={API_KEY}&regions=us&markets={prop}&oddsFormat=american"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        for market in data.get('bookmakers', [{}])[0].get('markets', []):
            if market['key'] == prop:
                return market['outcomes']
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching prop odds: {e}")
        return None

@st.cache(ttl=3600)  # Cache for 1 hour
def get_player_stats(player_name, trend_period=5):
    """
    Fetch player stats from Ball Don't Lie API.
    
    Args:
        player_name (str): Name of the player.
        trend_period (int): Number of recent games to fetch (default: 5).
    
    Returns:
        list or None: List of recent stats if available, None otherwise.
    """
    # Get player ID
    player_response = requests.get(f"{BALL_DONT_LIE_BASE_URL}/players?search={player_name}")
    if player_response.status_code != 200 or not player_response.json()['data']:
        return None
    player_id = player_response.json()['data'][0]['id']
    
    # Get recent stats
    stats_response = requests.get(
        f"{BALL_DONT_LIE_BASE_URL}/stats?player_ids[]={player_id}&per_page={trend_period}"
    )
    if stats_response.status_code != 200:
        return None
    stats = stats_response.json()['data']
    return stats

def predict_player_prop(player_name, prop, prop_line, game, trend_period=5):
    """
    Predict player prop outcome using stats from Ball Don't Lie API.
    
    Args:
        player_name (str): Name of the player.
        prop (str): Prop type (e.g., player_points).
        prop_line (float): Prop line value.
        game (dict): Game information.
        trend_period (int): Number of recent games for trend analysis (default: 5).
    
    Returns:
        dict or None: Prediction details if successful, None otherwise.
    """
    stats = get_player_stats(player_name, trend_period)
    if not stats:
        return None
    
    # Extract relevant stat (e.g., points, assists, etc.)
    stat_key = prop.split('_')[1]  # e.g., 'points' from 'player_points'
    historical_values = [stat.get(stat_key, 0) for stat in stats]
    if not historical_values:
        return None
    
    historical_avg = sum(historical_values) / len(historical_values)
    std_dev = (sum((x - historical_avg) ** 2 for x in historical_values) / len(historical_values)) ** 0.5 if len(historical_values) > 1 else 0
    opponent_factor = 1.05  # Placeholder for opponent adjustment
    predicted_mean = historical_avg * opponent_factor
    
    prob_over = 1 - norm.cdf(prop_line, loc=predicted_mean, scale=std_dev)
    prediction = "Over" if prob_over > 0.5 else "Under"
    confidence = prob_over * 100 if prob_over > 0.5 else (1 - prob_over) * 100
    
    odds_data = get_player_prop_odds(game['id'], prop)
    odds = "-110"  # Default if no odds found
    if odds_data:
        for outcome in odds_data:
            if outcome['name'] == player_name and float(outcome['point']) == prop_line:
                odds = str(outcome['price'])
                break
    
    edge = predicted_mean - prop_line if prediction == "Over" else prop_line - predicted_mean
    risk_level = get_risk_level(int(odds))
    
    return {
        "prediction": prediction,
        "confidence": confidence,
        "odds": odds,
        "prop_line": prop_line,
        "insight": f"Based on a {trend_period}-game trend, adjusted for opponent.",
        "edge": edge,
        "risk_level": risk_level
    }

def predict_game_outcome(game):
    """
    Predict game outcomes (moneyline, spread, over/under).
    
    Args:
        game (dict): Game information.
    
    Returns:
        dict or None: Prediction details if successful, None otherwise.
    """
    bookmakers = game['bookmakers']
    if not bookmakers:
        return None
    
    fanduel = next((b for b in bookmakers if b['key'] == 'fanduel'), bookmakers[0])
    markets = {m['key']: m for m in fanduel['markets']}
    
    # Moneyline
    h2h = markets.get('h2h', {})
    h2h_outcomes = h2h.get('outcomes', [])
    home_odds = next((o['price'] for o in h2h_outcomes if o['name'] == game['home_team']), 100)
    away_odds = next((o['price'] for o in h2h_outcomes if o['name'] == game['away_team']), 100)
    home_prob = odds_to_implied_prob(home_odds)
    win_prob = home_prob if home_odds < away_odds else 1 - home_prob
    moneyline_team = game['home_team'] if home_odds < away_odds else game['away_team']
    moneyline_odds = home_odds if home_odds < away_odds else away_odds
    
    # Spread
    spreads = markets.get('spreads', {})
    spread_outcomes = spreads.get('outcomes', [])
    spread_line = next((o['point'] for o in spread_outcomes if o['name'] == game['home_team']), 0)
    spread_odds = next((o['price'] for o in spread_outcomes if o['name'] == game['home_team']), -110)
    predicted_spread = spread_line  # Simplified
    
    # Over/Under
    totals = markets.get('totals', {})
    total_outcomes = totals.get('outcomes', [])
    total_line = total_outcomes[0]['point'] if total_outcomes else 200
    over_odds = next((o['price'] for o in total_outcomes if o['name'] == 'Over'), -110)
    predicted_total = total_line  # Simplified
    
    return {
        "moneyline": {
            "team": moneyline_team,
            "win_prob": win_prob,
            "odds": str(moneyline_odds),
            "edge": win_prob - odds_to_implied_prob(moneyline_odds)
        },
        "spread": {
            "line": spread_line,
            "odds": str(spread_odds),
            "edge": predicted_spread - spread_line if spread_line < 0 else spread_line - predicted_spread
        },
        "over_under": {
            "prediction": "Over" if predicted_total > total_line else "Under",
            "line": total_line,
            "odds": str(over_odds),
            "edge": abs(predicted_total - total_line)
        }
    }

def odds_to_implied_prob(odds):
    """
    Convert American odds to implied probability.
    
    Args:
        odds (int): American odds value.
    
    Returns:
        float: Implied probability.
    """
    if odds > 0:
        return 100 / (odds + 100)
    return -odds / (-odds + 100)

def get_risk_level(odds):
    """
    Determine risk level based on odds.
    
    Args:
        odds (int): Odds value.
    
    Returns:
        str: Risk level indicator.
    """
    if odds <= -200:
        return "🟢 Safe (-300 to -200)"
    elif odds <= -180:
        return "🟡 Moderate (-180 to +100)"
    elif odds >= 251:
        return "🔴 Very High Risk (+251 or above)"
    return "🟡 Moderate (-180 to +100)"

# Example usage (remove in production)
if __name__ == "__main__":
    st.write("Utils module for NBA betting prediction system")
​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​
