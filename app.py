import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd

# --- Helper Functions for The Odds API ---

def get_api_key():
    """Retrieves the API key from Streamlit secrets."""
    try:
        return st.secrets["ODDS_API_KEY"]
    except KeyError:
        st.error("Please add your Odds API key to Streamlit secrets (e.g., in secrets.toml or Streamlit Cloud settings).")
        st.stop()

@st.cache_data(ttl=60)  # Cache for 60 seconds to respect API rate limits
def fetch_games(date):
    """Fetches NBA games for the given date from The Odds API."""
    api_key = get_api_key()
    sport = 'basketball_nba'
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={api_key}®ions=us&markets=h2h"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        games = [f"{event['home_team']} v {event['away_team']}" for event in data]
        return games
    else:
        st.error(f"Failed to fetch games: HTTP {response.status_code}")
        return []

@st.cache_data(ttl=30)  # Cache for 30 seconds since odds update frequently
def fetch_odds(game):
    """Fetches live odds for the selected game from The Odds API."""
    api_key = get_api_key()
    sport = 'basketball_nba'
    regions = 'us'
    markets = 'h2h,spreads,totals'  # Moneyline, Spread, Over/Under
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={api_key}®ions={regions}&markets={markets}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for event in data:
            if f"{event['home_team']} v {event['away_team']}" == game:
                bookmakers = event['bookmakers']
                # Find best Moneyline (highest odds for home team)
                best_ml = max(bookmakers, key=lambda b: b['markets'][0]['outcomes'][0]['price'])
                # Find best Spread (lowest point for favorite, assuming home team is favorite if point < 0)
                best_spread = min(bookmakers, key=lambda b: b['markets'][1]['outcomes'][0]['point'] if b['markets'][1]['outcomes'][0]['name'] == event['home_team'] else float('inf'))
                # Find best Over/Under (lowest total points)
                best_ou = min(bookmakers, key=lambda b: b['markets'][2]['outcomes'][0]['point'])
                return {
                    'moneyline': {'book': best_ml['title'], 'odds': best_ml['markets'][0]['outcomes'][0]['price']},
                    'spread': {'book': best_spread['title'], 'point': best_spread['markets'][1]['outcomes'][0]['point'], 'odds': best_spread['markets'][1]['outcomes'][0]['price']},
                    'over_under': {'book': best_ou['title'], 'total': best_ou['markets'][2]['outcomes'][0]['point'], 'odds': best_ou['markets'][2]['outcomes'][0]['price']}
                }
        return {"error": "Game not found in API response"}
    else:
        return {"error": f"API request failed with status {response.status_code}"}

@st.cache_data(ttl=30)  # Cache for 30 seconds since props update frequently
def fetch_player_props(game):
    """Fetches live player props for the selected game from The Odds API."""
    api_key = get_api_key()
    sport = 'basketball_nba'
    regions = 'us'
    markets = 'player_points,player_rebounds,player_assists,player_threes'  # Example player prop markets
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={api_key}®ions={regions}&markets={markets}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        props = []
        for event in data:
            if f"{event['home_team']} v {event['away_team']}" == game:
                for bookmaker in event['bookmakers']:
                    for market in bookmaker['markets']:
                        for outcome in market['outcomes']:
                            props.append({
                                'player': outcome['description'],
                                'prop_type': market['key'].replace('player_', ''),  # e.g., 'points'
                                'value': outcome.get('point', 'N/A'),  # Some props may not have a point value
                                'odds': outcome['price'],
                                'bookmaker': bookmaker['title']
                            })
        return props if props else [{"error": "No player props available for this game"}]
    else:
        return [{"error": f"API request failed with status {response.status_code}"}]

# --- Streamlit App ---

st.title("NBA Betting Analysis Tool")
st.write("Select a game from the sidebar to view live odds and player props powered by The Odds API.")

# Sidebar for game selection
st.sidebar.title("Game Selection")
date_option = st.sidebar.radio("Select Date", ["Today", "Tomorrow"])
date = datetime.now().strftime('%Y-%m-%d') if date_option == "Today" else (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
games = fetch_games(date)
selected_game = st.sidebar.selectbox("Select Game", games)

# Main content
if selected_game:
    # Display live odds
    st.header("Best Available Odds")
    odds = fetch_odds(selected_game)
    if "error" in odds:
        st.error(odds["error"])
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Moneyline", f"{odds['moneyline']['odds']} ({odds['moneyline']['book']})")
        with col2:
            st.metric("Spread", f"{odds['spread']['point']} ({odds['spread']['book']}, {odds['spread']['odds']})")
        with col3:
            st.metric("Over/Under", f"{odds['over_under']['total']} ({odds['over_under']['book']}, {odds['over_under']['odds']})")

    # Display live player props
    st.header("Player Props")
    props = fetch_player_props(selected_game)
    if props and "error" not in props[0]:
        df = pd.DataFrame(props)
        st.dataframe(df[['player', 'prop_type', 'value', 'odds', 'bookmaker']], use_container_width=True)
    else:
        st.error(props[0]["error"])

else:
    st.write("Please select a game from the sidebar to view live data.")

# Sidebar footer
st.sidebar.markdown("---")
st.sidebar.write("This app uses live data from The Odds API. Ensure your API key is configured in Streamlit secrets.")
