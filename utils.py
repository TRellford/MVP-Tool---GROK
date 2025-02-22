import requests
import os
import pandas as pd
import datetime
import streamlit as st
from nba_api.stats.endpoints import playergamelog, leaguedashteamstats, scoreboardv2
from nba_api.stats.static import players

@st.cache_data(ttl=3600)

def get_games_by_date(target_date):
    """Fetch NBA games for a specific date and return matchups in 'Away Team at Home Team' format."""
    formatted_date = target_date.strftime("%Y-%m-%d")
    
    try:
        # Fetch scoreboard data for the given date
        scoreboard = scoreboardv2.ScoreboardV2(game_date=formatted_date)
        game_header_df = scoreboard.game_header.get_data_frame()
        line_score_df = scoreboard.line_score.get_data_frame()

        # Handle cases where no games are found
        if game_header_df.empty or line_score_df.empty:
            return ["⚠️ No games available or data not yet released."]

        # Create a mapping of TEAM_ID to 'CITY_NAME TEAM_NAME'
        team_id_to_name = {
            row['TEAM_ID']: f"{row['TEAM_CITY_NAME']} {row['TEAM_NAME']}"
            for _, row in line_score_df.iterrows()
            if pd.notna(row['TEAM_CITY_NAME']) and pd.notna(row['TEAM_NAME'])
        }

        # Construct game matchups using team names
        game_list = []
        for _, game in game_header_df.iterrows():
            home_team_id = game.get('HOME_TEAM_ID')
            visitor_team_id = game.get('VISITOR_TEAM_ID')
            
            home_team_name = team_id_to_name.get(home_team_id, "Unknown Home Team")
            visitor_team_name = team_id_to_name.get(visitor_team_id, "Unknown Visitor Team")
            
            matchup = f"{visitor_team_name} at {home_team_name}"
            game_list.append(matchup)

        return game_list if game_list else ["⚠️ No games scheduled for this date."]

    except Exception as e:
        return [f"❌ Error fetching games: {str(e)}"]


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

def fetch_best_props(player_name, trend_length):
    """Fetches the best player props based on stats trends & defensive matchups."""
    player_stats = fetch_player_data(player_name, trend_length)

    if isinstance(player_stats, dict) and "error" in player_stats:
        return {"error": "Player stats unavailable."}

    # Get Opponent Defensive Ratings
    try:
        team_defense = leaguedashteamstats.LeagueDashTeamStats(season="2023-24").get_data_frames()[0]
    except Exception as e:
        return {"error": f"Failed to fetch team defense data: {str(e)}"}

    # Find Weakest Defenses in Points, Assists, Rebounds
    weakest_teams = {
        "points": team_defense.sort_values("OPP_PTS", ascending=False).head(3)["TEAM_NAME"].tolist(),
        "assists": team_defense.sort_values("OPP_AST", ascending=False).head(3)["TEAM_NAME"].tolist(),
        "rebounds": team_defense.sort_values("OPP_REB", ascending=False).head(3)["TEAM_NAME"].tolist(),
    }

    # Ensure player_stats has valid data
    if player_stats.empty or "Points" not in player_stats.columns:
        return {"error": "Player stats missing or incomplete."}

    # Determine Best Prop Based on Trends & Matchups
    best_prop = max(
        [("Points", player_stats["Points"].mean()), 
         ("Assists", player_stats["Assists"].mean()), 
         ("Rebounds", player_stats["Rebounds"].mean())],
        key=lambda x: x[1]
    )

    return {
        "best_prop": best_prop[0],
        "average_stat": round(best_prop[1], 1),
        "weak_defensive_teams": weakest_teams.get(best_prop[0].lower(), [])
    }

def fetch_game_predictions(game_selection):
    """Fetches AI-generated Moneyline, Spread, and Over/Under predictions for a selected game."""
    
    if not game_selection or "vs" not in game_selection:
        return {"error": "Invalid game selection. Please select a valid game."}

    home_team, away_team = game_selection.split(" vs ")

    # Example AI-generated predictions (Replace with real model later)
    predictions = {
        "Game": f"{home_team} vs {away_team}",
        "Moneyline": f"{home_team} to win (Win Probability: 55%)",
        "Spread": f"{home_team} -3.5 (-110)",
        "Over/Under": f"Over 225.5 (-108)",
        "Edge Detector": "🔥 AI Model suggests home team should be -5.0 favorites, creating a 1.5-point edge."
    }
    
    return predictions

def fetch_sharp_money_trends(game_selection):
    """Fetches betting line movement & sharp money trends from Sports Data API."""
    
    if not game_selection or "vs" not in game_selection:
        return {"error": "Invalid game selection. Please select a valid game."}

    url = f"https://sportsdata.io/api/betting-trends?game={game_selection}"
    
    response = requests.get(url, headers={"Authorization": f"Bearer {os.getenv('BETTING_API_KEY')}"})
    
    if response.status_code != 200:
        return {"error": f"Failed to fetch data: {response.text}"}
    
    data = response.json()
    
    return {
        "Public Bets %": data.get("public_bets", "N/A"),
        "Sharp Money %": data.get("sharp_money", "N/A"),
        "Line Movement": data.get("line_movement", "N/A")
    }
def fetch_sgp_builder(game_selection, props, multi_game=False):
    """Generates an optimized Same Game Parlay (SGP) based on player props & correlation scores."""

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

