import streamlit as st
import datetime
import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder

st.set_page_config(page_title="NBA Betting AI", layout="wide")

# --- Cache Function to Store NBA Games ---
@st.cache_data(ttl=3600)  # Cache for 1 hour (games don’t change)
def get_games_by_date(target_date):
    """Fetches NBA games scheduled for a given date."""
    game_finder = leaguegamefinder.LeagueGameFinder(season_nullable="2023-24")
    games = game_finder.get_data_frames()[0]

    # Convert game date format
    games["GAME_DATE"] = pd.to_datetime(games["GAME_DATE"])

    # Filter games by the target date
    filtered_games = games[games["GAME_DATE"].dt.date == target_date.date()]

    # Extract team matchups
    game_list = [f"{row['TEAM_ABBREVIATION']} vs {row['MATCHUP'].split()[-1]}" for _, row in filtered_games.iterrows()]
    
    return game_list if game_list else ["No games available"]

# --- Get Today's & Tomorrow's Dates ---
today = datetime.datetime.today()
tomorrow = today + datetime.timedelta(days=1)

# --- Fetch Games (Using Cached Function) ---
todays_games = get_games_by_date(today)
tomorrows_games = get_games_by_date(tomorrow)

# --- UI ---
st.title("🏀 NBA Betting AI - Game Selection")

# Radio button for date selection
selected_date = st.radio("Choose Game Date:", ["Today's Games", "Tomorrow's Games"])

# Update dropdown based on the selected date
game_selection = st.selectbox("Select a Game:", todays_games if selected_date == "Today's Games" else tomorrows_games)

st.success(f"📅 You selected: {game_selection}")
