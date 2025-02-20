import requests
import streamlit as st

def get_api_key():
    """Retrieve the API key from Streamlit secrets."""
    try:
        key = st.secrets["ODDS_API_KEY"]
        st.write(f"API Key retrieved: {key[:4]}... (partially hidden for security)")  # Debug
        return key
    except KeyError:
        st.error("API key not found in Streamlit secrets.")
        st.stop()

@st.cache_data(ttl=60)
def fetch_games(date):
    """Fetch NBA games for a given date from The Odds API."""
    api_key = get_api_key()
    sport = 'basketball_nba'
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={api_key}®ions=us&markets=h2h"
    st.write(f"Requesting URL: {url}")  # Debug: Remove in production
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        st.write(f"Received {len(data)} games from API")  # Debug
        games = [f"{event['home_team']} vs {event['away_team']}" for event in data]
        return games
    else:
        st.error(f"Failed to fetch games: HTTP {response.status_code}")
        st.write(f"API Response: {response.text}")  # Debug
        return []

@st.cache_data(ttl=30)
def fetch_odds(game):
    # ... (unchanged unless needed for further debugging)
    pass

@st.cache_data(ttl=30)
def fetch_player_props(game):
    # ... (unchanged unless needed for further debugging)
    pass
