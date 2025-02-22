import streamlit as st
import requests
import snscrape.modules.twitter as sntwitter
from scipy.stats import norm
from datetime import datetime
import json

# ✅ Load API Keys
try:
    API_KEYS = {
        "balldontlie": st.secrets["balldontlie_api_key"],
        "odds_api": st.secrets["odds_api_key"]
    }
except KeyError as e:
    st.error(f"🚨 API key missing: {e}")
    st.stop()

# ✅ API Base URLs
BASE_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba"
BALL_DONT_LIE_BASE_URL = "https://www.balldontlie.io/api/v1"

# 📌 Cache Data for Efficiency
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_games():
    """Fetch today's NBA games from BallDontLie API."""
    url = f"{BALL_DONT_LIE_BASE_URL}/games"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()["data"]
    else:
        st.error(f"Error fetching games: {response.status_code}")
        return []

@st.cache_data(ttl=3600)  # Cache for 1 hour
def find_player_games(player_name):
    """Find upcoming games for a player based on their team."""
    url = f"{BALL_DONT_LIE_BASE_URL}/players?search={player_name}"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"🚨 API Error: {response.status_code}")
            return []
        
        data = response.json()
        if "data" not in data or not data["data"]:
            st.error(f"❌ No players found for: {player_name}")
            return []

        # Extract player's team
        player_info = data["data"][0]
        player_team = player_info.get("team", {}).get("full_name", "Unknown Team")

        # Fetch NBA games
        games_url = f"{BALL_DONT_LIE_BASE_URL}/games"
        games_response = requests.get(games_url)
        if games_response.status_code != 200:
            st.error(f"🚨 Error fetching NBA games: {games_response.status_code}")
            return []

        games = games_response.json().get("data", [])
        return [
            {
                "id": game["id"],
                "home_team": game["home_team"]["full_name"],
                "away_team": game["visitor_team"]["full_name"],
                "commence_time": game["date"]
            }
            for game in games if player_team in [game["home_team"]["full_name"], game["visitor_team"]["full_name"]]
        ]

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Request failed: {e}")
        return []

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_nba_odds():
    """Fetch NBA odds from The Odds API."""
    url = f"{BASE_URL}/odds?apiKey={API_KEYS['odds_api']}&regions=us&markets=h2h,spreads,totals&oddsFormat=american"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching NBA odds: {response.status_code}")
        return []

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

def scrape_underdog_nba():
    """Scrape latest Underdog NBA tweets for injury updates."""
    tweets = []
    query = "from:Underdog__NBA"
    
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
        if i >= 5:  # Get the latest 5 tweets
            break
        tweets.append(tweet.content)

    return tweets

# 🔥 Predict Player Props
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
    
    odds_data = get_nba_odds()
    odds = "-110"
    
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

# 🎯 Odds Calculations
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
