import requests
import os
import pandas as pd
import datetime
import streamlit as st
from nba_api.stats.endpoints import playergamelog, leaguedashteamstats, scoreboardv2
from nba_api.stats.static import players
from nba_api.stats.endpoints import commonplayerinfo

# --- Cache Game Fetching ---
@st.cache_data(ttl=3600)
def get_games_by_date(target_date):
    """Fetch NBA games using Scoreboard API."""
    formatted_date = target_date.strftime("%Y-%m-%d")
    try:
        scoreboard = scoreboardv2.ScoreboardV2(game_date=formatted_date)
        games_df = scoreboard.get_data_frames()[0]
        if games_df.empty:
            return ["No games available"]
        return [f"{row['GAMECODE'][:3]} vs {row['GAMECODE'][3:6]}" for _, row in games_df.iterrows()]
    except Exception as e:
        return [f"Error fetching games: {str(e)}"]

# --- Cache Player List ---
@st.cache_data(ttl=3600)
def get_all_players():
    return players.get_players()

# --- Fetch Player Stats ---
@st.cache_data(ttl=600)
def fetch_player_data(player_name, trend_length):
    player_dict = get_all_players()
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

# --- Fetch Best Player Props ---
def fetch_best_props(player_name, trend_length):
    player_stats = fetch_player_data(player_name, trend_length)
    if "error" in player_stats:
        return {"error": "Player stats unavailable."}
    team_defense = leaguedashteamstats.LeagueDashTeamStats(season="2023-24").get_data_frames()[0]
    weakest_teams = {
        "points": team_defense.sort_values("OPP_PTS", ascending=False).head(3)["TEAM_NAME"].tolist(),
        "assists": team_defense.sort_values("OPP_AST", ascending=False).head(3)["TEAM_NAME"].tolist(),
        "rebounds": team_defense.sort_values("OPP_REB", ascending=False).head(3)["TEAM_NAME"].tolist()
    }
    best_prop = max([("Points", player_stats["Points"].mean()), ("Assists", player_stats["Assists"].mean()), ("Rebounds", player_stats["Rebounds"].mean())], key=lambda x: x[1])
    return {"best_prop": best_prop[0], "average_stat": round(best_prop[1], 1), "weak_defensive_teams": weakest_teams[best_prop[0].lower()]}

# --- Fetch Game Predictions ---
def fetch_game_predictions(game_selection):
    return {"prediction": f"AI-generated prediction for {game_selection}"}

# --- Fetch Same Game Parlay (SGP) Builder ---
def fetch_sgp_builder(game_selection, sgp_props):
    return {"sgp": f"SGP Built for {game_selection} with {', '.join(sgp_props)}"}
