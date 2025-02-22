import streamlit as st
import json
from utils import get_games, get_nba_odds, scrape_underdog_nba

# 🎨 Streamlit UI
st.title("🏀 NBA Betting Insights & Injury Updates")

# 🔥 Fetch and display games
games = get_games()
if games:
    st.subheader("📆 Today's Games")
    for game in games:
        st.write(f"🏀 {game['home_team']['full_name']} vs {game['visitor_team']['full_name']} - {game['date']}")
else:
    st.warning("No games found.")

# 🔥 Fetch and display NBA odds
odds_data = get_nba_odds()
if odds_data:
    st.subheader("📊 NBA Betting Odds")
    st.json(odds_data)

# 🔥 Scrape and display Underdog NBA injury updates
st.subheader("🚨 Latest Injury Updates (Underdog NBA)")
injury_updates = scrape_underdog_nba()
if injury_updates:
    for update in injury_updates:
        st.write(f"🗞 {update}")
else:
    st.warning("No injury updates found.")
