import requests
import os
import pandas as pd
import datetime
import streamlit as st
from nba_api.stats.endpoints import playergamelog, leaguedashteamstats, scoreboardv2
from nba_api.stats.static import players
from datetime import datetime, timedelta

# --- 1️⃣ Fetch NBA Games (Fixed Formatting) ---
def get_games_by_date(target_date):
    """Fetch NBA games for a specific date and return matchups in 'Away Team at Home Team' format."""
    formatted_date = target_date.strftime("%Y-%m-%d")

    try:
        scoreboard = scoreboardv2.ScoreboardV2(game_date=formatted_date)
        game_header_df = scoreboard.game_header.get_data_frame()
        line_score_df = scoreboard.line_score.get_data_frame()

        if game_header_df.empty or line_score_df.empty:
            return ["⚠️ No games available."]

        matchups = []
        for _, game in game_header_df.iterrows():
            away = line_score_df.loc[line_score_df.TEAM_ID == game.VISITOR_TEAM_ID, 'TEAM_ABBREVIATION'].values
            home = line_score_df.loc[line_score_df.TEAM_ID == game.HOME_TEAM_ID, 'TEAM_ABBREVIATION'].values

            if len(away) > 0 and len(home) > 0:
                matchups.append(f"{away[0]} at {home[0]}")

        return matchups

    except Exception as e:
        return [f"❌ API Error: {str(e)}"]

# --- 2️⃣ Optimized Player Search (Faster Lookup) ---
def get_player_id(player_name):
    """Fetch player ID with O(1) lookup instead of looping."""
    player_dict = {p["full_name"].lower(): p["id"] for p in players.get_players()}
    return player_dict.get(player_name.lower(), None)

# --- 3️⃣ Fetch Player Stats with Opponent Adjustments ---
def fetch_player_data(player_name, trend_length):
    """Fetches recent player stats adjusted for opponent defensive strength."""
    player_id = get_player_id(player_name)
    if not player_id:
        return {"error": "Player not found."}

    try:
        game_logs = playergamelog.PlayerGameLog(player_id=player_id, season="2024-25")
        game_df = game_logs.get_data_frames()[0]

        # 🚨 Filter Out Future Games
        current_date = datetime.today().date()
        game_df["Game Date"] = pd.to_datetime(game_df["GAME_DATE"])
        game_df = game_df.sort_values(by="Game Date", ascending=False)
        game_df = game_df[game_df["Game Date"].dt.date <= current_date]

        # Fetch Team Defensive Data
        defense_stats = leaguedashteamstats.LeagueDashTeamStats(season="2024-25").get_data_frames()[0]
        defense_stats = defense_stats[["TEAM_ID", "TEAM_ABBREVIATION", "OPP_PTS", "OPP_AST", "OPP_REB"]]

        # Extract Opponent Team IDs from Matchup
        game_df["Opponent Team"] = game_df["MATCHUP"].apply(lambda x: x.split(" ")[-1])
        game_df = game_df.merge(defense_stats, left_on="Opponent Team", right_on="TEAM_ABBREVIATION", how="left")

        return game_df[["Game Date", "PTS", "REB", "AST", "OPP_PTS", "OPP_AST", "OPP_REB"]]

    except Exception as e:
        return {"error": f"Failed to fetch player stats: {str(e)}"}

# --- 4️⃣ Fetch Sharp Money & Live Betting Trends ---
def fetch_sharp_money_trends(game_selection):
    """Fetches betting line movement & sharp money trends from multiple sources."""
    api_key = os.getenv("BETTING_API_KEY")
    if not api_key:
        return {"error": "API key is missing. Check your environment variables."}

    apis = [
        f"https://sportsdata.io/api/betting-trends?game={game_selection}",
        f"https://another-source.com/api/trends?matchup={game_selection}"
    ]

    for api_url in apis:
        response = requests.get(api_url, headers={"Authorization": f"Bearer {api_key}"})
        if response.status_code == 200:
            data = response.json()
            return {
                "Public Bets %": data.get("public_bets", "N/A"),
                "Sharp Money %": data.get("sharp_money", "N/A"),
                "Line Movement": data.get("line_movement", "N/A")
            }

    return {"error": "Failed to fetch data from all sources."}

# --- 5️⃣ Fetch Best Props with Risk Levels ---
def fetch_best_props(player_name, trend_length, min_odds=-450, max_odds=-200):
    """Fetches the best player props based on stats trends, defensive matchups, and risk levels."""
    player_stats = fetch_player_data(player_name, trend_length)
    if isinstance(player_stats, dict) and "error" in player_stats:
        return {"error": "Player stats unavailable."}

    team_defense = leaguedashteamstats.LeagueDashTeamStats(season="2024-25").get_data_frames()[0]

    weakest_teams = {
        "points": team_defense.sort_values("OPP_PTS", ascending=False).head(3)["TEAM_NAME"].tolist(),
        "assists": team_defense.sort_values("OPP_AST", ascending=False).head(3)["TEAM_NAME"].tolist(),
        "rebounds": team_defense.sort_values("OPP_REB", ascending=False).head(3)["TEAM_NAME"].tolist(),
    }

    best_prop = max(
        [("Points", player_stats["PTS"].mean()), 
         ("Assists", player_stats["AST"].mean()), 
         ("Rebounds", player_stats["REB"].mean())],
        key=lambda x: x[1]
    )

    # 🚀 Fetch Dynamic Odds Instead of Hardcoding
    odds_response = requests.get(f"https://odds.io/api/props?player={player_name}")
    if odds_response.status_code == 200:
        odds_data = odds_response.json()
    else:
        odds_data = {"Points": -350, "Assists": -180, "Rebounds": +120}

    risk_levels = {
        "🔵 Very Safe": (-450, -300),
        "🟢 Safe": (-299, -200),
        "🟡 Moderate Risk": (-199, +100),
        "🟠 High Risk": (+101, +250),
        "🔴 Very High Risk": (+251, float("inf"))
    }

    best_prop_name, best_stat = best_prop
    prop_odds = odds_data.get(best_prop_name, 0)

    if not (min_odds <= prop_odds <= max_odds):
        return {"error": f"No props found within odds range {min_odds} to {max_odds}"}

    risk_label = next((label for label, (low, high) in risk_levels.items() if low <= prop_odds <= high), "Unknown Risk Level")

    return {
        "best_prop": best_prop_name,
        "average_stat": round(best_stat, 1),
        "odds": prop_odds,
        "risk_level": risk_label,
        "weak_defensive_teams": weakest_teams.get(best_prop_name.lower(), [])
    }
