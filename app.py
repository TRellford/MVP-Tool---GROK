import streamlit as st
import requests
import snscrape.modules.twitter as sntwitter
from nba_api.stats.endpoints import commonplayerinfo, playergamelogs
from nba_api.stats.static import players, teams
from scipy.stats import norm
from datetime import datetime
import json

# 🔑 API KEYS (User needs to add their BallDontLie & Odds API keys)
try:
    BALLDONTLIE_API_KEY = st.secrets["balldontlie_api_key"]
    ODDS_API_KEY = st.secrets["odds_api_key"]
except KeyError:
    st.error("API key(s) missing. Add them to Streamlit secrets.")
    st.stop()

# 🌐 API Base URLs
BALL_DONT_LIE_BASE_URL = "https://www.balldontlie.io/api/v1"
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba"

# ✅ Scrape Latest Tweets from @Underdog__NBA for Injury Updates
@st.cache_data(ttl=300)  # Cache for 5 minutes
def scrape_underdog_nba_tweets():
    """Scrape @Underdog__NBA latest tweets for injury & lineup updates."""
    tweets = []
    query = "from:Underdog__NBA"
    for tweet in sntwitter.TwitterSearchScraper(query).get_items():
        tweets.append(tweet.content)
        if len(tweets) == 10:  # Limit to last 10 tweets
            break
    return tweets

# ✅ Get NBA Player Stats (Last 5, 10, 15 Games) from NBA API
@st.cache_data(ttl=3600)
def get_nba_player_stats(player_name, num_games=5):
    """Fetch a player's last 5, 10, or 15 game logs from NBA API."""
    all_players = players.get_players()
    player = next((p for p in all_players if p["full_name"].lower() == player_name.lower()), None)
    
    if not player:
        return None

    player_id = player["id"]
    gamelogs = playergamelogs.PlayerGameLogs(player_id=player_id, season_nullable="2023-24", per_mode_simple="PerGame").get_dict()
    
    if not gamelogs or "resultSets" not in gamelogs or len(gamelogs["resultSets"]) == 0:
        return None

    logs = gamelogs["resultSets"][0]["rowSet"][:num_games]
    return logs

# ✅ Find Player's Team and Upcoming Games
@st.cache_data(ttl=3600)
def find_player_games(player_name):
    """Find upcoming games for a player based on their team."""
    url = f"{BALL_DONT_LIE_BASE_URL}/players?search={player_name}"
    response = requests.get(url)

    if response.status_code != 200 or "data" not in response.json():
        return []

    player_data = response.json()["data"]
    if not player_data:
        return []

    player_info = player_data[0]
    player_team = player_info.get("team", {}).get("full_name", "Unknown Team")

    # Fetch NBA schedule
    games_url = f"{BALL_DONT_LIE_BASE_URL}/games"
    games_response = requests.get(games_url)

    if games_response.status_code != 200:
        return []

    games = games_response.json().get("data", [])

    # Filter games where the player's team is playing
    player_games = [
        {
            "id": game["id"],
            "home_team": game["home_team"]["full_name"],
            "away_team": game["visitor_team"]["full_name"],
            "date": game["date"]
        }
        for game in games
        if player_team in [game["home_team"]["full_name"], game["visitor_team"]["full_name"]]
    ]

    return player_games

# ✅ Get Player Prop Odds from The Odds API
def get_player_prop_odds(game_id, prop):
    """Fetch player prop odds from The Odds API."""
    url = f"{ODDS_API_BASE_URL}/events/{game_id}/odds?apiKey={ODDS_API_KEY}&regions=us&markets={prop}&oddsFormat=american"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        for market in data.get("bookmakers", [{}])[0].get("markets", []):
            if market["key"] == prop:
                return market["outcomes"]
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching prop odds: {e}")
        return None

# ✅ Predict Player Prop Based on Stats
def predict_player_prop(player_name, prop, prop_line, game, num_games=5):
    """Predict player prop outcome using last N games."""
    stats = get_nba_player_stats(player_name, num_games)
    if not stats:
        return None

    stat_key = prop.split("_")[1]
    historical_values = [stat.get(stat_key, 0) for stat in stats]

    if not historical_values:
        return None

    avg = sum(historical_values) / len(historical_values)
    std_dev = (sum((x - avg) ** 2 for x in historical_values) / len(historical_values)) ** 0.5 if len(historical_values) > 1 else 0
    predicted_mean = avg * 1.05  # Placeholder for opponent adjustment

    prob_over = 1 - norm.cdf(prop_line, loc=predicted_mean, scale=std_dev)
    prediction = "Over" if prob_over > 0.5 else "Under"
    confidence = prob_over * 100 if prob_over > 0.5 else (1 - prob_over) * 100

    odds_data = get_player_prop_odds(game["id"], prop)
    odds = "-110"
    if odds_data:
        for outcome in odds_data:
            if outcome["name"] == player_name and float(outcome["point"]) == prop_line:
                odds = str(outcome["price"])
                break

    return {
        "prediction": prediction,
        "confidence": confidence,
        "odds": odds,
        "prop_line": prop_line,
        "insight": f"Based on last {num_games} games."
    }

# ✅ Streamlit UI
st.title("🏀 Initial MVP Tool - NBA Betting Insights")

# 🚀 Injury & Lineup Updates from @Underdog__NBA
st.subheader("🔴 Real-Time Injury & Lineup Updates")
tweets = scrape_underdog_nba_tweets()
for tweet in tweets:
    st.write(f"📝 {tweet}")

# 📊 Player Prop Predictions
st.subheader("📈 Player Prop Predictions")
player_name = st.text_input("Enter Player Name")
prop_type = st.selectbox("Select Prop", ["points", "rebounds", "assists"])
prop_line = st.number_input("Set Prop Line", min_value=0.0, step=0.5)

if st.button("Get Prediction"):
    games = find_player_games(player_name)
    if not games:
        st.error(f"No upcoming games found for {player_name}.")
    else:
        game = games[0]  # Assume next game
        prediction = predict_player_prop(player_name, prop_type, prop_line, game)
        if prediction:
            st.write(f"📊 Prediction: **{prediction['prediction']}**")
            st.write(f"🔢 Confidence: **{prediction['confidence']:.2f}%**")
            st.write(f"💰 Odds: **{prediction['odds']}**")
            st.write(f"📌 Insight: {prediction['insight']}")
        else:
            st.error("Failed to generate prediction.")

# 🔄 Update Button
if st.button("🔄 Refresh Injury Reports"):
    scrape_underdog_nba_tweets()
    st.experimental_rerun()
