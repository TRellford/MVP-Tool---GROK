import streamlit as st
import requests
import pandas as pd
import json
from scipy.stats import norm
from nba_api.stats.endpoints import commonplayerinfo, playergamelogs
from nba_api.stats.static import players, teams

# 🔥 Load API Keys
try:
    BALDONTLIE_API_KEY = st.secrets["balldontlie_api_key"]
    ODDS_API_KEY = st.secrets["odds_api_key"]
except KeyError:
    st.error("🚨 API keys missing! Set them in `.streamlit/secrets.toml`.")
    st.stop()

# ✅ API Base URLs
BALL_DONT_LIE_BASE_URL = "https://www.balldontlie.io/api/v1"
NBA_ODDS_BASE_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba"

# 📌 Cache Data for Efficiency
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_games():
    """Fetch today's NBA games from BallDontLie API."""
    url = f"{BALL_DONT_LIE_BASE_URL}/games"
    response = requests.get(url)
    
    if response.status_code == 200:
        games = response.json()["data"]
        return games
    else:
        st.error(f"Error fetching games: {response.status_code}")
        return []

@st.cache_data(ttl=3600)
def get_player_stats(player_name):
    """Fetch player stats from BallDontLie API."""
    url = f"{BALL_DONT_LIE_BASE_URL}/players?search={player_name}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()["data"]
        if data:
            player_id = data[0]["id"]
            stats_url = f"{BALL_DONT_LIE_BASE_URL}/season_averages?player_ids[]={player_id}"
            stats_response = requests.get(stats_url)
            return stats_response.json().get("data", [])
        else:
            st.warning(f"Player '{player_name}' not found.")
            return []
    else:
        st.error(f"Error fetching player stats: {response.status_code}")
        return []

@st.cache_data(ttl=1800)
def get_nba_odds():
    """Fetch NBA odds from The Odds API."""
    url = f"{NBA_ODDS_BASE_URL}/odds?apiKey={ODDS_API_KEY}&regions=us&markets=h2h,spreads,totals&oddsFormat=american"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching NBA odds: {response.status_code}")
        return []

@st.cache_data(ttl=600)  # Cache for 10 minutes
def scrape_underdog_nba():
    """Scrape latest Underdog NBA tweets for injury updates using Nitter."""
    url = "https://nitter.net/Underdog__NBA/rss"  # Using Nitter for scraping
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Extract latest 5 tweets
        tweets = response.text.split("<title>")[2:7]
        return [tweet.split("</title>")[0] for tweet in tweets]
    
    except Exception as e:
        st.error(f"⚠️ Failed to fetch tweets: {e}")
        return []

# 🎨 Streamlit UI
st.title("🏀 NBA Betting Insights & Injury Updates")

# 🔥 Fetch and display games
games = get_games()
if games:
    st.subheader("📆 Today's Games")
    for game in games:
        st.write(f"🏀 {game['home_team']['full_name']} vs {game['visitor_team']['full_name']} - {game['date']}")
else:
    st.warning("No games found.")

# 🔥 Fetch and display NBA odds
odds_data = get_nba_odds()
if odds_data:
    st.subheader("📊 NBA Betting Odds")
    st.json(odds_data)

# 🔥 Fetch and display player stats
player_name = st.text_input("🔍 Search Player Stats:")
if player_name:
    player_stats = get_player_stats(player_name)
    if player_stats:
        st.subheader(f"📈 {player_name} Season Averages")
        st.json(player_stats)

# 🔥 Scrape and display Underdog NBA injury updates
st.subheader("🚨 Latest Injury Updates (Underdog NBA)")
injury_updates = scrape_underdog_nba()
if injury_updates:
    for update in injury_updates:
        st.write(f"🗞 {update}")
else:
    st.warning("No injury updates found.")
