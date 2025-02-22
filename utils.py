import requests
import os
from bs4 import BeautifulSoup
from nba_api.stats.endpoints import playergamelog, commonplayerinfo
from nba_api.stats.static import players

# API Keys
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# --- Fetch Player Stats from NBA API ---
def fetch_player_data(player_name, trend_length):
    """ Fetches real-time player stats from NBA API """
    
    # Get Player ID from Name
    player_dict = players.get_players()
    player = next((p for p in player_dict if p["full_name"].lower() == player_name.lower()), None)

    if not player:
        return {"error": "Player not found. Please check the spelling."}

    player_id = player["id"]

    # Get Last X Games Data
    game_log = playergamelog.PlayerGameLog(player_id=player_id, season="2023-24", season_type_all_star="Regular Season")
    game_data = game_log.get_data_frames()[0].head(trend_length)

    # Extract Stats
    stats = []
    for _, row in game_data.iterrows():
        stats.append({
            "game_date": row["GAME_DATE"],
            "points": row["PTS"],
            "rebounds": row["REB"],
            "assists": row["AST"],
            "three_pointers_made": row["FG3M"],
            "minutes": row["MIN"]
        })

    return {
        "player_name": player_name,
        "trend_length": trend_length,
        "stats": stats
    }

# --- Fetch Live Betting Odds ---
def fetch_odds(entity, prop_type):
    """ Fetches real-time odds for players & games """
    url = f"https://api.odds.io/v4/{'players' if ' ' in entity else 'games'}/{entity}/odds?markets={prop_type}"
    response = requests.get(url, headers={"Authorization": f"Bearer {ODDS_API_KEY}"})
    
    if response.status_code != 200:
        return {"error": f"API Error: {response.status_code}, Response: {response.text}"}
    
    return response.json()

# --- Scrape Underdog NBA Twitter for Injuries ---
def scrape_underdog_twitter(game):
    """ Scrapes Underdog NBA Twitter via Nitter """
    url = "https://nitter.net/Underdog__NBA"
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": "Failed to retrieve Twitter data"}

    soup = BeautifulSoup(response.text, 'html.parser')
    tweets = soup.find_all('div', class_='timeline-item')

    relevant_tweets = [tweet.text.strip() for tweet in tweets if game in tweet.text]
    
    return relevant_tweets[:3]  # Return last 3 tweets

# --- AI-Based Betting Edge Detector ---
def detect_betting_edge(ai_predicted_line, sportsbook_odds):
    """ Compares AI-predicted lines with sportsbook odds to find value bets """
    edge_found = False
    risk_level = "Unknown"

    # Extract odds and AI predictions
    odds = sportsbook_odds.get("odds", -110)  # Default to -110 if missing
    ai_line = ai_predicted_line.get("prediction", "N/A")

    # Detect Edge - AI vs. Sportsbook
    if abs(ai_predicted_line["adjusted_spread"] - sportsbook_odds["spread"]) > 1.5:
        edge_found = True

    # Assign risk levels based on odds
    if -300 <= odds <= -200:
        risk_level = "🟢 Safe"
    elif -180 <= odds <= +100:
        risk_level = "🟡 Moderate"
    elif +101 <= odds <= +250:
        risk_level = "🟠 High Risk"
    elif odds >= +251:
        risk_level = "🔴 Very High Risk"

    return {
        "betting_edge_found": edge_found,
        "ai_predicted_line": ai_line,
        "sportsbook_odds": odds,
        "risk_level": risk_level
    }

# --- AI Model Processing for Real-Time Bets ---
def run_ai_models(player_data, odds_data, prop_type, confidence_threshold):
    """ Runs AI models to process real NBA data & predict betting outcomes """

    if "error" in player_data or "error" in odds_data:
        return {"error": "Missing or invalid data for AI model"}

    # Calculate AI Adjusted Spread (Example: Adjusting based on past games)
    avg_stat = sum(stat[prop_type.lower()] for stat in player_data["stats"]) / len(player_data["stats"])

    # AI Prediction Output
    ai_prediction = {
        "player": player_data["player_name"],
        "prop": prop_type,
        "prediction": f"Over {avg_stat:.1f} (-110)",
        "confidence_score": confidence_threshold,
        "insight": f"{player_data['player_name']} has averaged {avg_stat:.1f} {prop_type.lower()} per game over the last {player_data['trend_length']} games.",
        "adjusted_spread": avg_stat  # AI's suggested optimal line
    }

    # Run Betting Edge Detection
    edge_analysis = detect_betting_edge(ai_prediction, odds_data)

    # Merge AI Prediction with Betting Edge Insights
    ai_prediction.update(edge_analysis)

    return ai_prediction
