import requests
import pandas as pd
import datetime
import streamlit as st
from bs4 import BeautifulSoup  # Web scraping for Nitter
from nba_api.stats.endpoints import playergamelog, leaguedashteamstats, scoreboardv2
from nba_api.stats.static import players
from datetime import datetime

# --- Securely Load API Keys from Streamlit Secrets ---
ODDS_API_KEY = st.secrets["apiKey"]
BALDONTLIE_API_KEY = st.secrets["ball_dont_lie_api_key"]

# --- Function to Fetch NBA Games by Date ---
@st.cache_data(ttl=3600)
def get_games_by_date(target_date):
    formatted_date = target_date.strftime("%Y-%m-%d")
    
    try:
        scoreboard = scoreboardv2.ScoreboardV2(game_date=formatted_date)
        game_header_df = scoreboard.game_header.get_data_frame()
        line_score_df = scoreboard.line_score.get_data_frame()

        if game_header_df.empty or line_score_df.empty:
            return ["⚠️ No games available or data not yet released."]

        team_id_to_name = {
            row['TEAM_ID']: f"{row['TEAM_CITY_NAME']} {row['TEAM_NAME']}"
            for _, row in line_score_df.iterrows()
            if pd.notna(row['TEAM_CITY_NAME']) and pd.notna(row['TEAM_NAME'])
        }

        matchups = [
            f"{team_id_to_name.get(row['VISITOR_TEAM_ID'], 'Unknown Team')} vs {team_id_to_name.get(row['HOME_TEAM_ID'], 'Unknown Team')}"
            for _, row in game_header_df.iterrows()
        ]

        return matchups

    except Exception as e:
        return [f"❌ Error fetching games: {str(e)}"]

# --- Fetch Player Metadata from BallDontLie API ---
def fetch_player_metadata(player_name):
    url = f"https://www.balldontlie.io/api/v1/players?search={player_name}"
    headers = {"Authorization": f"Bearer {BALDONTLIE_API_KEY}"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": f"Failed to fetch player data: {response.text}"}

    data = response.json()
    
    if not data.get("data"):
        return {"error": "Player not found."}

    return data["data"][0]

def fetch_player_game_logs(player_name):
    """Fetches recent player stats (points, assists, rebounds, 3PT made)."""
    
    # Get Player ID
    player_dict = players.get_players()
    player_id = next((p["id"] for p in player_dict if p["full_name"].lower() == player_name.lower()), None)
    
    if not player_id:
        return {"error": "Player not found in NBA API."}
    
    try:
        # Fetch game logs
        game_logs = playergamelog.PlayerGameLog(player_id=player_id, season="2023-24", season_type_all_star="Regular Season")
        game_df = game_logs.get_data_frames()[0]

        # Convert & Sort Game Date
        game_df["Game Date"] = pd.to_datetime(game_df["GAME_DATE"])
        game_df = game_df.sort_values(by="Game Date", ascending=False)

        return game_df[["Game Date", "PTS", "AST", "REB", "FG3M"]]

    except Exception as e:
        return {"error": f"Failed to fetch player stats: {str(e)}"}

# --- Fetch Prop Betting Lines from Odds API ---
def fetch_betting_odds(game_selection):
    url = f"https://sportsdata.io/api/betting-odds?game={game_selection}"
    headers = {"Authorization": f"Bearer {ODDS_API_KEY}"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": f"Failed to fetch betting odds: {response.text}"}

    return response.json()

# --- Fetch Opponent Defensive Data ---
def fetch_defensive_data():
    try:
        team_defense = leaguedashteamstats.LeagueDashTeamStats(season="2023-24").get_data_frames()[0]
        return team_defense
    except Exception as e:
        return {"error": f"Failed to fetch team defense data: {str(e)}"}

# --- Fetch Injury & Roster Updates from Nitter ---
def fetch_injury_updates():
    """Scrapes Underdog NBA injury updates from Nitter."""
    
    nitter_url = "https://nitter.net/Underdog__NBA"
    
    try:
        response = requests.get(nitter_url, headers={"User-Agent": "Mozilla/5.0"})
        
        if response.status_code != 200:
            return {"error": f"Failed to scrape Nitter. Status: {response.status_code}"}
        
        soup = BeautifulSoup(response.text, "html.parser")
        tweets = soup.find_all("div", class_="tweet-content")  # Locate tweets
        
        injury_updates = []
        
        for tweet in tweets:
            text = tweet.get_text(strip=True)
            if "injury" in text.lower() or "out" in text.lower() or "available" in text.lower():
                injury_updates.append(text)

        return injury_updates if injury_updates else ["No injury updates found."]
    
    except Exception as e:
        return {"error": f"Failed to fetch injury updates: {str(e)}"}

# --- First Basket Prediction (Tip-Off Analysis) ---
def fetch_first_basket_data():
    try:
        scoreboard = scoreboardv2.ScoreboardV2()
        game_header_df = scoreboard.game_header.get_data_frame()

        tip_off_winners = game_header_df.groupby("HOME_TEAM_ID")["HOME_TEAM_WINS"].mean()
        return tip_off_winners.sort_values(ascending=False).to_dict()

    except Exception as e:
        return {"error": f"Failed to fetch first basket data: {str(e)}"}

# --- Streamlit UI ---
st.title("🏀 NBA Betting & Prop Analyzer with Full Data Integrations")

selected_date = st.date_input("📅 Select a Game Date", datetime.today())
game_list = get_games_by_date(selected_date)
selected_game = st.selectbox("🎮 Choose a Game", game_list)

player_name = st.text_input("🏀 Enter NBA Player Name")

risk_level_filter = st.selectbox(
    "⚠️ Select Risk Level",
    ["All", "🔵 Very Safe", "🟢 Safe", "🟡 Moderate Risk", "🟠 High Risk", "🔴 Very High Risk"]
)

if st.button("🔍 Fetch Player Info"):
    player_data = fetch_player_metadata(player_name)
    st.write(player_data)

if st.button("📊 Fetch Betting Odds"):
    odds_data = fetch_betting_odds(selected_game)
    st.write(odds_data)

if st.button("⚠️ Fetch Injury Updates (Nitter)"):
    injuries = fetch_injury_updates()
    st.write(injuries)

if st.button("🛑 Fetch First Basket Trends"):
    first_basket_data = fetch_first_basket_data()
    st.write(first_basket_data)
