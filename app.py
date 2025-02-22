import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import utils  # Import backend functions from utils.py

# --- Streamlit App Title ---
st.set_page_config(page_title="NBA Betting & Prop Analyzer", layout="wide")
st.title("🏀 NBA Betting & Prop Analyzer")

# --- User Inputs ---
selected_date = st.date_input("📅 Select a Game Date", datetime.today())
game_list = utils.get_games_by_date(selected_date)
selected_game = st.selectbox("🎮 Choose a Game", game_list)

player_name = st.text_input("🏀 Enter NBA Player Name")

# --- Risk Level Filter ---
risk_level_filter = st.selectbox(
    "⚠️ Select Risk Level",
    ["All", "🔵 Very Safe", "🟢 Safe", "🟡 Moderate Risk", "🟠 High Risk", "🔴 Very High Risk"]
)

# --- Function to Generate Player Graphs ---
def plot_player_stats(player_stats, category, title):
    """Generates a bar graph for the given player stat category."""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(player_stats["Game Date"], player_stats[category], color="royalblue")
    ax.set_xlabel("Game Date")
    ax.set_ylabel(category)
    ax.set_title(title)
    plt.xticks(rotation=45)
    return fig

# --- Fetch Player Info & Display Graphs ---
if st.button("🔍 Fetch Player Info"):
    player_data = utils.fetch_player_metadata(player_name)
    st.write(player_data)

    # Fetch Player Game Logs
    player_stats = utils.fetch_player_game_logs(player_name)
    
    if isinstance(player_stats, dict) and "error" in player_stats:
        st.error("Player stats unavailable.")
    else:
        # Create Tabs for 5, 10, 15 Game Trends
        tab1, tab2, tab3 = st.tabs(["Last 5 Games", "Last 10 Games", "Last 15 Games"])

        with tab1:
            st.subheader("📊 Last 5 Games Performance")
            st.pyplot(plot_player_stats(player_stats.head(5), "PTS", "Last 5 Games - Points"))
            st.pyplot(plot_player_stats(player_stats.head(5), "AST", "Last 5 Games - Assists"))
            st.pyplot(plot_player_stats(player_stats.head(5), "REB", "Last 5 Games - Rebounds"))
            st.pyplot(plot_player_stats(player_stats.head(5), "FG3M", "Last 5 Games - 3PT Made"))

        with tab2:
            st.subheader("📊 Last 10 Games Performance")
            st.pyplot(plot_player_stats(player_stats.head(10), "PTS", "Last 10 Games - Points"))
            st.pyplot(plot_player_stats(player_stats.head(10), "AST", "Last 10 Games - Assists"))
            st.pyplot(plot_player_stats(player_stats.head(10), "REB", "Last 10 Games - Rebounds"))
            st.pyplot(plot_player_stats(player_stats.head(10), "FG3M", "Last 10 Games - 3PT Made"))

        with tab3:
            st.subheader("📊 Last 15 Games Performance")
            st.pyplot(plot_player_stats(player_stats.head(15), "PTS", "Last 15 Games - Points"))
            st.pyplot(plot_player_stats(player_stats.head(15), "AST", "Last 15 Games - Assists"))
            st.pyplot(plot_player_stats(player_stats.head(15), "REB", "Last 15 Games - Rebounds"))
            st.pyplot(plot_player_stats(player_stats.head(15), "FG3M", "Last 15 Games - 3PT Made"))

# --- Fetch Betting Odds ---
if st.button("📊 Fetch Betting Odds"):
    odds_data = utils.fetch_betting_odds(selected_game)
    st.write(odds_data)

# --- Fetch Injury Updates ---
if st.button("⚠️ Fetch Injury Updates (Nitter)"):
    injuries = utils.fetch_injury_updates()
    st.write(injuries)

# --- Fetch First Basket Trends ---
if st.button("🛑 Fetch First Basket Trends"):
    first_basket_data = utils.fetch_first_basket_data()
    st.write(first_basket_data)
