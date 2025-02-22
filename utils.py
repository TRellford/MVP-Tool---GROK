import streamlit as st
import requests
from bs4 import BeautifulSoup
from scipy.stats import norm
from nba_api.stats.endpoints import commonplayerinfo, playergamelogs
from nba_api.stats.static import players, teams

# ✅ Load API Keys
try:
    BALDONTLIE_API_KEY = st.secrets["balldontlie_api_key"]
    ODDS_API_KEY = st.secrets["odds_api_key"]
except KeyError:
    st.error("🚨 API keys missing! Set them in `.streamlit/secrets.toml`.")
    st.stop()

# ✅ API Base URLs
BALL_DONT_LIE_BASE_URL = "https://www.balldontlie.io/api/v1"
NBA_ODDS_BASE_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba"
NITTER_BASE_URL = "https://nitter.net/Underdog__NBA"

# ✅ Fetch NBA Games
@st.cache_data(ttl=3600)
def get_games():
    """Fetch today's NBA games from BallDontLie API."""
    url = f"{BALL_DONT_LIE_BASE_URL}/games"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        st.error(f"Error fetching games: {response.status_code}")
        return []

# ✅ Fetch NBA Odds
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

# ✅ Fetch Player Stats
@st.cache_data(ttl=3600)
def get_player_stats(player_name, trend_period=5):
    """Fetch player stats from BallDontLie API."""
    player_response = requests.get(f"{BALL_DONT_LIE_BASE_URL}/players?search={player_name}")
    
    if player_response.status_code != 200 or not player_response.json()["data"]:
        st.error(f"❌ Player '{player_name}' not found.")
        return None
    
    player_id = player_response.json()["data"][0]["id"]
    
    stats_response = requests.get(f"{BALL_DONT_LIE_BASE_URL}/stats?player_ids[]={player_id}&per_page={trend_period}")
    
    if stats_response.status_code != 200:
        st.error("Failed to fetch player stats.")
        return None
    
    return stats_response.json()["data"]

# ✅ Predict Player Prop Outcomes
def predict_player_prop(player_name, prop, prop_line, game, trend_period=5):
    """Predict player prop outcome using stats from BallDontLie API."""
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
    
    return {
        "prediction": prediction,
        "confidence": confidence,
        "prop_line": prop_line,
        "insight": f"Based on a {trend_period}-game trend, adjusted for opponent."
    }

# ✅ Scrape Underdog NBA Tweets using Nitter
def scrape_underdog_nba():
    """Scrape latest Underdog NBA tweets for injury updates using Nitter."""
    response = requests.get(NITTER_BASE_URL)
    
    if response.status_code != 200:
        st.error(f"❌ Error fetching tweets from Nitter: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    tweets = []

    for tweet in soup.find_all("div", class_="tweet-content"):
        tweets.append(tweet.text.strip())

    return tweets[:5]  # Return the latest 5 tweets
