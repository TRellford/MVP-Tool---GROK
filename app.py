import streamlit as st
import pandas as pd
from utils import (
    get_games, 
    get_player_stats, 
    get_nba_odds, 
    scrape_underdog_nba, 
    predict_player_prop
)

# 🎯 Streamlit Page Title
st.title("🏀 NBA Betting Insights & Injury Updates")

# 📌 Sidebar for User Input
st.sidebar.header("🔍 Search Options")
player_name = st.sidebar.text_input("Enter a Player Name:")
prop = st.sidebar.selectbox("Select a Prop Category:", ["Points", "Rebounds", "Assists", "3PT Made"])
prop_line = st.sidebar.number_input("Set Prop Line:", min_value=0.0, step=0.5)

# ✅ Fetch & Display Today's Games
st.subheader("📆 Today's NBA Games")
games = get_games()
if games:
    for game in games:
        st.write(f"🏀 {game['home_team']['full_name']} vs {game['visitor_team']['full_name']} - {game['date']}")
else:
    st.warning("No games found.")

# ✅ Fetch & Display NBA Odds (with Correct API Key Parameter)
st.subheader("📊 NBA Betting Odds")
odds_data = get_nba_odds()
if odds_data:
    st.json(odds_data)

# ✅ Fetch & Display Player Stats
if player_name:
    st.subheader(f"📈 {player_name} Season Averages")
    player_stats = get_player_stats(player_name)
    
    if player_stats:
        df = pd.DataFrame(player_stats)
        st.dataframe(df)
    else:
        st.warning(f"No stats found for {player_name}.")

# ✅ Predict Player Props
if player_name and prop and prop_line:
    st.subheader(f"🔮 Prediction: {player_name}'s {prop}")
    selected_game = games[0] if games else None  # Use the first game found
    prediction = predict_player_prop(player_name, prop, prop_line, selected_game)

    if prediction:
        st.write(f"**Prediction:** {prediction['prediction']}")
        st.write(f"**Confidence:** {prediction['confidence']:.2f}%")
        st.write(f"**Odds:** {prediction['odds']}")
        st.write(f"**Edge:** {prediction['edge']:.2f}")
        st.write(f"**Risk Level:** {prediction['risk_level']}")
    else:
        st.warning("No prediction available.")

# ✅ Fetch & Display Injury Updates from Underdog NBA
st.subheader("🚨 Latest Injury Updates (Underdog NBA)")
injury_updates = scrape_underdog_nba()
if injury_updates:
    for update in injury_updates:
        st.write(f"🗞 {update}")
else:
    st.warning("No injury updates found.")
