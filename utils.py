import streamlit as st
import requests
from bs4 import BeautifulSoup
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
