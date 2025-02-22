import requests
import os
import pandas as pd
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from nba_api.stats.endpoints import playergamelog, leaguedashteamstats
from nba_api.stats.static import players
from nba_api.stats.endpoints import commonplayerinfo
import streamlit as st

# API Keys
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# --- Cache Player List to Reduce API Calls ---
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_all_players():
    """Fetches and caches the list of all NBA players."""
    return players.get_players()

# --- Fetch Player Stats (With Optimized Calls) ---
@st.cache_data(ttl=600)  # Cache for 10 minutes to reduce API load
def fetch_player_data(player_name, trend_length):
    """ Fetches real-time player stats from NBA API with caching """

    # Get Cached Player List
    player_dict = get_all_players()
    player = next((p for p in player_dict if p["full_name"].lower() == player_name.lower()), None)

    if not player:
        return {"error": "Player not found. Please check the spelling."}

    player_id = player["id"]

    # Get Last X Games Data
    game_log = playergamelog.PlayerGameLog(player_id=player_id, season="2023-24", season_type_all_star="Regular Season")
    game_data = game_log.get_data_frames()[0].head(trend_length)

    # Convert to DataFrame
    stats_df = pd.DataFrame({
        "Game Date": pd.to_datetime(game_data["GAME_DATE"]),
        "Points": game_data["PTS"],
        "Rebounds": game_data["REB"],
        "Assists": game_data["AST"],
        "3PT Made": game_data["FG3M"]
    })

    # Calculate Moving Averages (5-game rolling)
    stats_df["Points MA"] = stats_df["Points"].rolling(window=5, min_periods=1).mean()
    stats_df["Rebounds MA"] = stats_df["Rebounds"].rolling(window=5, min_periods=1).mean()
    stats_df["Assists MA"] = stats_df["Assists"].rolling(window=5, min_periods=1).mean()

    return stats_df

# --- Fetch Live Betting Odds ---
def fetch_odds(entity, prop_type):
    """ Fetches real-time odds for players & games """
    url = f"https://api.odds.io/v4/{'players' if ' ' in entity else 'games'}/{entity}/odds?markets={prop_type}"
    response = requests.get(url, headers={"Authorization": f"Bearer {ODDS_API_KEY}"})
    
    if response.status_code != 200:
        return {"error": f"API Error: {response.status_code}, Response: {response.text}"}
    
    return response.json()

# --- Optimized Auto-Fetch Best Player Props ---
def fetch_best_props(player_name, trend_length):
    """ Auto-selects best player props based on stats trends & defensive matchups """

    # Use Cached Stats Instead of Refetching
    player_stats = fetch_player_data(player_name, trend_length)

    if "error" in player_stats:
        return {"error": "Player stats not available."}

    # Get Opponent Defensive Ratings
    team_defense = leaguedashteamstats.LeagueDashTeamStats(season="2023-24")
    defense_df = team_defense.get_data_frames()[0]

    # Find Weakest Defenses in Points, Assists, Rebounds
    weakest_teams = {
        "points": defense_df.sort_values("OPP_PTS", ascending=False).head(3)["TEAM_NAME"].tolist(),
        "assists": defense_df.sort_values("OPP_AST", ascending=False).head(3)["TEAM_NAME"].tolist(),
        "rebounds": defense_df.sort_values("OPP_REB", ascending=False).head(3)["TEAM_NAME"].tolist(),
    }

    # Determine Best Prop Based on Trends & Matchups
    best_prop = max(
        [("Points", player_stats["Points"].mean()), ("Assists", player_stats["Assists"].mean()), ("Rebounds", player_stats["Rebounds"].mean())],
        key=lambda x: x[1]
    )

    return {
        "best_prop": best_prop[0],
        "average_stat": round(best_prop[1], 1),
        "weak_defensive_teams": weakest_teams[best_prop[0].lower()]
    }
