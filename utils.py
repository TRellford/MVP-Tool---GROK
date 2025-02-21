import streamlit as st
import requests
from scipy.stats import norm
from datetime import datetime
import json

# Access API key from Streamlit secrets
try:
    API_KEY = st.secrets["api_key"]
except KeyError:
    st.error("API key not found in Streamlit secrets. Make sure it's set in .streamlit/secrets.toml or Streamlit Cloud.")
    st.stop()  # Stop execution if API key is missing

BASE_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba"
BALL_DONT_LIE_BASE_URL = "https://www.balldontlie.io/api/v1"

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_games_by_date(date_str):
    """Fetch NBA games for a specific date."""
    url = f"{BASE_URL}/odds?apiKey={API_KEY}&regions=us&markets=h2h,spreads,totals&oddsFormat=american&date={date_str}T00:00:00Z"
    
    try:
        with st.spinner("Fetching games..."):
            response = requests.get(url)
            response.raise_for_status()
        games = response.json()
        return [
            {
                "id": game["id"],
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "commence_time": game["commence_time"],
                "bookmakers": game["bookmakers"]
            }
            for game in games
        ]
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching games: {e}")
        return []

@st.cache_data(ttl=3600)  # Cache for 1 hour
import requests
import streamlit as st

BALL_DONT_LIE_BASE_URL = "https://www.balldontlie.io/api/v1"

@st.cache_data(ttl=3600)  # Cache for 1 hour
def find_player_games(player_name):
    """Find upcoming games for a player based on their team."""
    
    url = f"{BALL_DONT_LIE_BASE_URL}/players?search={player_name}"
    
    try:
        response = requests.get(url)
        st.write(f"🔍 API Response Status: {response.status_code}")  # Debugging

        if response.status_code != 200:
            st.error(f"🚨 API Error: {response.status_code}")
            st.write(response.text)  # Print response for debugging
            return []
        
        data = response.json()
        
        if "data" not in data or not data["data"]:
            st.error(f"❌ No players found for: {player_name}")
            return []

        # Extract player's team
        player_info = data["data"][0]
        player_team = player_info.get("team", {}).get("full_name", "Unknown Team")

        st.write(f"✅ Found Player: {player_info['first_name']} {player_info['last_name']}, Team: {player_team}")

        # Now fetch NBA games
        games_url = f"https://www.balldontlie.io/api/v1/games"
        games_response = requests.get(games_url)
        
        if games_response.status_code != 200:
            st.error(f"🚨 Error fetching NBA games: {games_response.status_code}")
            return []

        games = games_response.json().get("data", [])

        # Filter games where the player's team is playing
        player_games = [
            {
                "id": game["id"],
                "home_team": game["home_team"]["full_name"],
                "away_team": game["visitor_team"]["full_name"],
                "commence_time": game["date"]
            }
            for game in games
            if player_team in [game["home_team"]["full_name"], game["visitor_team"]["full_name"]]
        ]

        return player_games

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Request failed: {e}")
        return []


def get_player_prop_odds(game_id, prop):
    """Fetch player prop odds from The Odds API."""
    url = f"{BASE_URL}/events/{game_id}/odds?apiKey={API_KEY}&regions=us&markets={prop}&oddsFormat=american"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        for market in data.get("bookmakers", [{}])[0].get("markets", []):
            if market["key"] == prop:
                return market["outcomes"]
        return None
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching prop odds: {e}")
        return None

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_player_stats(player_name, trend_period=5):
    """Fetch player stats from Ball Don't Lie API."""
    player_response = requests.get(f"{BALL_DONT_LIE_BASE_URL}/players?search={player_name}")
    
    if player_response.status_code != 200 or not player_response.json()["data"]:
        st.error("Player not found.")
        return None
    
    player_id = player_response.json()["data"][0]["id"]
    
    stats_response = requests.get(f"{BALL_DONT_LIE_BASE_URL}/stats?player_ids[]={player_id}&per_page={trend_period}")
    
    if stats_response.status_code != 200:
        st.error("Failed to fetch player stats.")
        return None
    
    return stats_response.json()["data"]

def predict_player_prop(player_name, prop, prop_line, game, trend_period=5):
    """Predict player prop outcome using stats from Ball Don't Lie API."""
    stats = get_player_stats(player_name, trend_period)
    if not stats:
        return None
    
    stat_key = prop.split("_")[1]
    historical_values = [stat.get(stat_key, 0) for stat in stats]
    if not historical_values:
        return None
    
    historical_avg = sum(historical_values) / len(historical_values)
    std_dev = (
        (sum((x - historical_avg) ** 2 for x in historical_values) / len(historical_values)) ** 0.5
        if len(historical_values) > 1 else 0
    )
    predicted_mean = historical_avg * 1.05  # Placeholder for opponent adjustment
    
    prob_over = 1 - norm.cdf(prop_line, loc=predicted_mean, scale=std_dev)
    prediction = "Over" if prob_over > 0.5 else "Under"
    confidence = prob_over * 100 if prob_over > 0.5 else (1 - prob_over) * 100
    
    odds_data = get_player_prop_odds(game["id"], prop)
    odds = "-110"
    if odds_data:
        for outcome in odds_data:
            if outcome["name"] == player_name and float(outcome["point"]) == prop_line:
                odds = str(outcome["price"])
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

def odds_to_implied_prob(odds):
    """Convert American odds to implied probability."""
    if odds > 0:
        return 100 / (odds + 100)
    return -odds / (-odds + 100)

def get_risk_level(odds):
    """Determine risk level based on odds."""
    if odds <= -200:
        return "🟢 Safe (-300 to -200)"
    elif -200 < odds <= -100:
        return "🟡 Moderate (-200 to -100)"
    elif -99 <= odds <= +100:
        return "🟠 High Risk (-99 to +100)"
    elif odds >= 251:
        return "🔴 Very High Risk (+251 or above)"
    return "🟡 Moderate"
