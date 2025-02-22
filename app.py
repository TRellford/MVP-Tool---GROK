import streamlit as st
from utils import fetch_player_data, fetch_odds, scrape_underdog_twitter, run_ai_models

st.set_page_config(page_title="NBA Betting AI", layout="wide")

# Title
st.title("🏀 AI-Powered NBA Betting Predictions")

# Sidebar for User Selection
betting_type = st.sidebar.selectbox(
    "Select Betting Type:",
    ["Player Search", "Multi-Game Props", "Game Predictions"]
)

# --- PLAYER PROP SEARCH ---
if betting_type == "Player Search":
    st.header("🔍 Player Prop Analysis")
    
    player_name = st.text_input("Enter Player Name (e.g., LeBron James)")
    prop_type = st.selectbox("Select Prop Type", ["Points", "Assists", "Rebounds", "3PT Made", "All"])
    confidence_threshold = st.slider("Confidence Score Filter (%)", 50, 100, 80)
    trend_length = st.radio("Trend Length", [5, 10, 15])

    if st.button("Get Prediction"):
        if not player_name:
            st.warning("Please enter a player name.")
        else:
            st.write("🔄 Fetching Data...")
            player_data = fetch_player_data(player_name, trend_length)
            odds_data = fetch_odds(player_name, prop_type)
            prediction = run_ai_models(player_data, odds_data, prop_type, confidence_threshold)
            st.success("✅ Prediction Ready!")

            st.subheader(f"📊 Prediction for {player_name}")
            st.json(prediction)

# --- MULTI-GAME PROP SELECTION ---
elif betting_type == "Multi-Game Props":
    st.header("📊 Multi-Game Prop Selections")
    
    games = st.text_area("Enter Game Matchups (e.g., BOS vs. MIA, LAL vs. GSW)", help="Separate matchups by commas")
    props_per_game = st.slider("Props Per Game", 1, 8, 3)
    confidence_threshold = st.slider("Confidence Score Filter (%)", 50, 100, 75)

    if st.button("Get Multi-Game Predictions"):
        if not games:
            st.warning("Please enter at least one game.")
        else:
            games_list = [game.strip() for game in games.split(",")]
            predictions = []
            for game in games_list:
                game_predictions = []
                for _ in range(props_per_game):
                    game_predictions.append(run_ai_models(fetch_player_data(game), fetch_odds(game), "all", confidence_threshold))
                predictions.append({game: game_predictions})

            st.success("✅ Multi-Game Predictions Ready!")
            st.json(predictions)

# --- GAME PREDICTIONS (Moneyline, Spread, O/U) ---
elif betting_type == "Game Predictions":
    st.header("📈 Game Predictions (Moneyline, Spread, O/U)")
    
    game = st.text_input("Enter Game Matchup (e.g., LAL vs. BOS)")
    
    if st.button("Get Game Predictions"):
        if not game:
            st.warning("Please enter a game matchup.")
        else:
            st.write("🔄 Fetching Data...")
            injury_news = scrape_underdog_twitter(game)
            odds_data = fetch_odds(game, "all")
            prediction = run_ai_models(None, odds_data, "game_prediction", 0)
            st.success("✅ Game Prediction Ready!")

            st.subheader(f"🏀 Prediction for {game}")
            st.json(prediction)

            if injury_news:
                st.subheader("🚨 Injury Updates")
                for news in injury_news:
                    st.write(f"📢 {news}")

st.sidebar.info("🔄 Data updates every few minutes to reflect live odds and AI predictions.")
