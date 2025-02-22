import requests
import os
import pandas as pd
import datetime
import streamlit as st
from nba_api.stats.endpoints import playergamelog, leaguedashteamstats, scoreboardv2
from nba_api.stats.static import players

# --- Cache Game Fetching ---
@st.cache_data(ttl=3600)
def get_games_by_date(target_date):
    """Fetch NBA games using Scoreboard API and display team names & game times."""
    formatted_date = target_date.strftime("%Y-%m-%d")
    try:
        scoreboard = scoreboardv2.ScoreboardV2(game_date=formatted_date)
        games_df = scoreboard.get_data_frames()[0]

        if games_df.empty:
            return ["No games available"]

        game_list = [f"{row['HOME_TEAM_NAME']} vs {row['VISITOR_TEAM_NAME']} - {row['GAME_STATUS_TEXT']}" for _, row in games_df.iterrows()]
        return list(set(game_list))  # Remove duplicates

    except Exception as e:
        return [f"Error fetching games: {str(e)}"]

# --- Fetch Player Stats ---
@st.cache_data(ttl=600)
def fetch_player_data(player_name, trend_length):
    """Fetch player stats from NBA API."""
    player_dict = players.get_players()
    player = next((p for p in player_dict if p["full_name"].lower() == player_name.lower()), None)

    if not player:
        return {"error": "Player not found."}

    player_id = player["id"]
    game_log = playergamelog.PlayerGameLog(player_id=player_id, season="2023-24")
    game_data = game_log.get_data_frames()[0].head(trend_length)

    return pd.DataFrame({
        "Game Date": pd.to_datetime(game_data["GAME_DATE"]),
        "Points": game_data["PTS"],
        "Rebounds": game_data["REB"],
        "Assists": game_data["AST"],
        "3PT Made": game_data["FG3M"]
    })

# --- Sharp Money & Line Movement Tracker ---
def fetch_sharp_money_trends(game_selection):
    """Fetches betting line movement & sharp money trends."""
    url = f"https://sportsdata.io/api/betting-trends?game={game_selection}"
    response = requests.get(url, headers={"Authorization": f"Bearer {os.getenv('BETTING_API_KEY')}"})

    if response.status_code != 200:
        return {"error": f"Failed to fetch data: {response.text}"}

    data = response.json()
    return {
        "Public Bets %": data["public_bets"],
        "Sharp Money %": data["sharp_money"],
        "Line Movement": data["line_movement"]
    }

# --- Fetch SGP Builder with Correlation Score ---
def fetch_sgp_builder(game_selection, props, multi_game=False):
    """Generates an optimized SGP based on player props & correlation scores."""
    correlation_scores = {
        "Points & Assists": 0.85, 
        "Rebounds & Blocks": 0.78,
        "3PT & Points": 0.92
    }

    prop_text = f"SGP+ for multiple games" if multi_game else f"SGP for {game_selection}"
    return {
        "SGP": prop_text,
        "Correlation Scores": {p: correlation_scores.get(p, "No correlation data") for p in props}
    }
