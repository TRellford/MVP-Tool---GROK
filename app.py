import streamlit as st
from utils import get_games, get_nba_odds, get_player_stats, predict_player_prop, scrape_underdog_nba

# 🎨 Streamlit UI
st.title("🏀 NBA Betting Insights & Injury Updates")

# 🔥 Fetch and display games
games = get_games()
if games:
    st.subheader("📆 Select an NBA Game")
    game_selection = st.selectbox(
        "Choose a game:",
        [f"{game['home_team']['full_name']} vs {game['visitor_team']['full_name']}" for game in games],
    )
else:
    st.warning("No games found.")

# 🔥 Fetch and display NBA odds
st.subheader("📊 NBA Betting Odds")
odds_data = get_nba_odds()
if odds_data:
    st.json(odds_data)
else:
    st.warning("No odds data available.")

# 🔥 Fetch and display player stats & prop predictions
st.subheader("🔍 Player Prop Analysis")
player_name = st.text_input("Enter a player's name:")

if player_name:
    player_stats = get_player_stats(player_name)
    
    if player_stats:
        st.subheader(f"📈 {player_name} Season Averages")
        st.json(player_stats)
        
        prop_type = st.selectbox("Choose a stat category:", ["points", "rebounds", "assists"])
        prop_line = st.number_input(f"Set the line for {prop_type}:", min_value=0.0, max_value=50.0, step=0.5)
        
        if st.button("🔮 Predict Outcome"):
            prediction = predict_player_prop(player_name, prop_type, prop_line, game_selection)
            if prediction:
                st.subheader(f"🔮 Prediction for {player_name}")
                st.write(f"📊 Prediction: **{prediction['prediction']}**")
                st.write(f"💯 Confidence: **{prediction['confidence']:.2f}%**")
                st.write(f"📌 Insight: {prediction['insight']}")
            else:
                st.error("Failed to generate prediction.")
    else:
        st.warning("No player stats found.")

# 🔥 Scrape and display Underdog NBA injury updates
st.subheader("🚨 Latest Injury Updates (Underdog NBA)")
injury_updates = scrape_underdog_nba()
if injury_updates:
    for update in injury_updates:
        st.write(f"🗞 {update}")
else:
    st.warning("No injury updates found.")
