import streamlit as st
import requests
import json
import tweepy
from nba_api.stats.endpoints import playergamelog, commonplayerinfo
from datetime import datetime, timedelta
from scipy.stats import norm

# Load API keys from Streamlit secrets
try:
    BALL_DONT_LIE_API_KEY = st.secrets["ball_dont_lie_api_key"]
    TWITTER_BEARER_TOKEN = st.secrets["twitter_bearer_token"]
except KeyError:
    st.error("API keys not found in Streamlit secrets. Ensure they are set in `.streamlit/secrets.toml`.")
    st.stop()

# API Endpoints
BALL_DONT_LIE_BASE_URL = "https://www.balldontlie.io/api/v1"
NBA_API_BASE_URL = "https://stats.nba.com/stats"

# Function to get NBA player stats (Last 5, 10, 15 games)
def get_nba_player_stats(player_name, trend_period=5):
    """Fetch player game logs from NBA API."""
    player_id = get_nba_player_id(player_name)
    if not player_id:
        st.error(f"Could not find player ID for {player_name}.")
        return None

    game_log = playergamelog.PlayerGameLog(player_id=player_id, season="2023-24", season_type_all_star="Regular Season").get_dict()
    stats = game_log["resultSets"][0]["rowSet"][:trend_period]

    return [
        {
            "date": stat[3],
            "points": stat[26],
            "rebounds": stat[20],
            "assists": stat[21],
            "three_pointers_made": stat[25]
        }
        for stat in stats
    ]

# Function to fetch player ID from NBA API
def get_nba_player_id(player_name):
    """Retrieve NBA player ID for API queries."""
    player_info = commonplayerinfo.CommonPlayerInfo().get_dict()
    for player in player_info["resultSets"][0]["rowSet"]:
        if player_name.lower() in player[3].lower():
            return player[0]
    return None

# Function to fetch player data from BallDontLie API
def get_player_info(player_name):
    url = f"{BALL_DONT_LIE_BASE_URL}/players?search={player_name}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "data" in data and data["data"]:
            return data["data"][0]
    return None

# Function to monitor Underdog NBA Twitter for real-time injuries
def monitor_underdog_twitter():
    """Fetch the latest tweets from Underdog NBA for injury updates."""
    client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
    query = "from:Underdog__NBA -is:retweet"
    tweets = client.search_recent_tweets(query=query, max_results=5)
    
    latest_updates = []
    if tweets.data:
        for tweet in tweets.data:
            latest_updates.append(tweet.text)
    
    return latest_updates

# Function to predict player props
def predict_player_prop(player_name, prop, prop_line, trend_period=5):
    """Predict player prop outcomes using NBA API stats."""
    stats = get_nba_player_stats(player_name, trend_period)
    if not stats:
        return None

    stat_key = {
        "points": "points",
        "rebounds": "rebounds",
        "assists": "assists",
        "three_pointers_made": "three_pointers_made"
    }.get(prop)

    if not stat_key:
        st.error(f"Invalid prop category: {prop}")
        return None

    historical_values = [stat[stat_key] for stat in stats]
    if not historical_values:
        return None

    avg_stat = sum(historical_values) / len(historical_values)
    std_dev = (sum((x - avg_stat) ** 2 for x in historical_values) / len(historical_values)) ** 0.5 if len(historical_values) > 1 else 0

    predicted_mean = avg_stat * 1.05  # Adjusted projection
    prob_over = 1 - norm.cdf(prop_line, loc=predicted_mean, scale=std_dev)
    prediction = "Over" if prob_over > 0.5 else "Under"
    confidence = prob_over * 100 if prob_over > 0.5 else (1 - prob_over) * 100

    return {
        "prediction": prediction,
        "confidence": confidence,
        "prop_line": prop_line,
        "trend_period": trend_period
    }

# Streamlit UI
st.title("NBA Betting Predictor 📊🔥")

player_name = st.text_input("Enter Player Name:")
prop_type = st.selectbox("Select Prop Type", ["points", "rebounds", "assists", "three_pointers_made"])
prop_line = st.number_input("Set Prop Line", min_value=0.0, step=0.5)
trend_period = st.selectbox("Trend Period", [5, 10, 15])

if st.button("Get Prediction"):
    prediction = predict_player_prop(player_name, prop_type, prop_line, trend_period)
    
    if prediction:
        st.subheader(f"Prediction: {prediction['prediction']}")
        st.write(f"Confidence: {prediction['confidence']:.2f}%")
        st.write(f"Using Last {prediction['trend_period']} Games")

    else:
        st.error("Could not generate a prediction. Please check player name and try again.")

# Display latest injury updates from Underdog NBA
st.subheader("🛑 Injury Updates from Underdog NBA:")
injury_updates = monitor_underdog_twitter()
if injury_updates:
    for update in injury_updates:
        st.write(f"🔹 {update}")
else:
    st.write("No recent injury updates found.")

