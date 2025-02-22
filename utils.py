import requests
import json
from bs4 import BeautifulSoup

# API Keys
BALLOONTLIE_API_KEY = "your_balldontlie_api_key"
ODDS_API_KEY = "your_odds_api_key"

# Fetch player stats
def fetch_player_data(player_name, trend_length):
    url = f"https://www.balldontlie.io/api/v1/players?search={player_name}"
    response = requests.get(url, headers={"Authorization": f"Bearer {BALLOONTLIE_API_KEY}"})
    player = response.json().get('data', [])[0]
    player_id = player.get("id")

    stats_url = f"https://www.balldontlie.io/api/v1/stats?player_ids[]={player_id}&per_page={trend_length}"
    stats_response = requests.get(stats_url, headers={"Authorization": f"Bearer {BALLOONTLIE_API_KEY}"})
    
    return stats_response.json().get('data', [])

# Fetch odds from Odds.io
def fetch_odds(entity, prop_type):
    url = f"https://api.odds.io/v4/{'players' if ' ' in entity else 'games'}/{entity}/odds?markets={prop_type}"
    response = requests.get(url, headers={"Authorization": f"Bearer {ODDS_API_KEY}"})
    return response.json()

# Scrape Underdog NBA Twitter using Nitter
def scrape_underdog_twitter(game):
    url = "https://nitter.net/Underdog__NBA"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    tweets = soup.find_all('div', class_='timeline-item')
    relevant_tweets = [tweet.text.strip() for tweet in tweets if game in tweet.text]
    
    return relevant_tweets[:3]  # Return last 3 tweets

# Betting Edge Detector
def detect_betting_edge(ai_predicted_line, sportsbook_odds):
    """ Compares AI-predicted lines with sportsbook odds to identify value bets. """
    edge_found = False
    risk_level = "Unknown"
    
    # Convert sportsbook odds to American format if needed
    odds = sportsbook_odds.get("odds", -110)  # Default to standard betting odds
    ai_line = ai_predicted_line.get("prediction", "N/A")

    # Check for discrepancies
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

# AI Model Simulations (Updated with Betting Edge Detection)
def run_ai_models(player_data, odds_data, prop_type, confidence_threshold):
    """ Runs AI models for predictions and includes betting edge analysis. """
    
    ai_prediction = {
        "player": player_data[0]["player"]["full_name"] if player_data else "N/A",
        "prop": prop_type,
        "prediction": "Over 25.5 (-110)",
        "confidence_score": 85,
        "insight": "This player has been exceeding expectations over the last 10 games.",
        "adjusted_spread": 24.5  # AI's suggested optimal line
    }

    # Run betting edge detector
    edge_analysis = detect_betting_edge(ai_prediction, odds_data)

    # Merge AI prediction with betting edge insights
    ai_prediction.update(edge_analysis)

    return ai_prediction
