import streamlit as st
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta
from utils import (
    get_games_by_date, fetch_player_data, fetch_best_props, 
    fetch_game_predictions, fetch_sgp_builder, fetch_sharp_money_trends
)

st.set_page_config(page_title="NBA Betting AI", layout="wide")

# --- Sidebar Navigation (Only Dropdown Menu) ---
st.sidebar.title("🔍 Navigation")
menu_option = st.sidebar.selectbox("Select a Section:", ["Player Search", "SGP", "SGP+", "Game Predictions"])

# --- Get Current and Next Day's Games ---
today = datetime.datetime.today().date()
tomorrow = today + timedelta(days=1)

todays_games = get_games_by_date(today)
tomorrows_games = get_games_by_date(tomorrow)

# --- Section 1: Player Search ---
if menu_option == "Player Search":
    st.header("🔍 Player Search & Prop Analysis")
    
    player_name = st.text_input("Enter Player Name (e.g., Kevin Durant)", key="player_search")
    
    selected_props = st.multiselect(
        "Choose Props to Display:",
        ["Points", "Rebounds", "Assists", "3PT Made", "Blocks", "Steals", "All"],
        default=["All"]
    )

    trend_length = st.radio("Select Trend Length", [5, 10, 15])

    if st.button("Get Player Stats"):
        if not player_name:
            st.warning("Please enter a player name.")
        else:
            stats_df = fetch_player_data(player_name, trend_length)

            if "error" in stats_df:
                st.error(stats_df["error"])
            else:
                st.write(f"📊 **Stats for {player_name}:**")

                if "All" in selected_props:
                    selected_props = ["Points", "Rebounds", "Assists", "3PT Made", "Blocks", "Steals"]

                # 📊 Ensure Dates Are Sorted Correctly
                stats_df["Game Date"] = pd.to_datetime(stats_df["Game Date"])
                stats_df = stats_df.sort_values(by="Game Date", ascending=False)  # Sort by recent games
                stats_df["Game Date"] = stats_df["Game Date"].dt.strftime("%b %d")  # Convert to 'Feb 22' format

                # 📊 Table of Averages for Selected Props
                st.subheader("📊 Average Stats Over Selected Games")
                prop_averages = {}

                for prop in selected_props:
                    if prop in stats_df.columns:
                        prop_averages[prop] = {
                            "Last 5 Games": round(stats_df[prop].iloc[:5].mean(), 1),
                            "Last 10 Games": round(stats_df[prop].iloc[:10].mean(), 1),
                            "Last 15 Games": round(stats_df[prop].iloc[:15].mean(), 1)
                        }

                # Convert to DataFrame & Display
                if prop_averages:
                    avg_df = pd.DataFrame(prop_averages).T
                    st.dataframe(avg_df.style.format("{:.1f}"))

                # 📊 Generate Graphs for Each Selected Prop
                for prop in selected_props:
                    if prop in stats_df.columns:
                        st.subheader(f"📊 {prop} - Last {trend_length} Games")
                        
                        # Create a Matplotlib Figure for Better Styling
                        fig, ax = plt.subplots(figsize=(8, 4))
                        ax.bar(stats_df["Game Date"], stats_df[prop], color="royalblue", alpha=0.8)
                        
                        # Improve Label Visibility
                        ax.set_xlabel("Game Date", fontsize=12)
                        ax.set_ylabel(prop, fontsize=12)
                        ax.set_title(f"{prop} Over Last {trend_length} Games", fontsize=14, fontweight="bold")
                        
                        # Rotate X-Axis Labels If Needed
                        ax.set_xticklabels(stats_df["Game Date"], rotation=30, ha="right", fontsize=10)
                        
                        # Display Graph
                        st.pyplot(fig)

# --- Section 2: SGP (Same Game Parlay - Only 1 Game Allowed) ---
elif menu_option == "SGP":
    st.header("🎯 Same Game Parlay (SGP) - One Game Only")
    
    selected_date = st.radio("Choose Game Date:", ["Today's Games", "Tomorrow's Games"], key="sgp_date")
    available_games = todays_games if selected_date == "Today's Games" else tomorrows_games
    
    selected_game = st.selectbox("Select a Game:", available_games, key="sgp_game")
    
    sgp_props = st.multiselect("Select Props for SGP:", ["Points", "Assists", "Rebounds", "3PT Made"])
    
    if st.button("Generate SGP"):
        sgp_result = fetch_sgp_builder(selected_game, sgp_props)
        st.write(sgp_result)

# --- Section 3: SGP+ (Multi-Game Parlay - 2 to 12 Games) ---
elif menu_option == "SGP+":
    st.header("🔥 Multi-Game Parlay (SGP+) - Select 2 to 12 Games")
    
    selected_games = st.multiselect("Select Games (Min: 2, Max: 12):", todays_games + tomorrows_games)

    if len(selected_games) < 2:
        st.warning("⚠️ You must select at least 2 games.")
    elif len(selected_games) > 12:
        st.warning("⚠️ You cannot select more than 12 games.")
    else:
        max_props_per_game = 24 // len(selected_games)
        props_per_game = st.slider(f"Choose Props Per Game (Max {max_props_per_game}):", 2, max_props_per_game)

        total_props = len(selected_games) * props_per_game
        if total_props > 24:
            st.error(f"🚨 Too many props selected! Max total allowed: 24. You selected {total_props}. Reduce props per game.")
        else:
            if st.button("Generate SGP+"):
                sgp_plus_result = fetch_sgp_builder(selected_games, props_per_game, multi_game=True)
                st.write(sgp_plus_result)

# --- Section 4: Game Predictions (ML, Spread, O/U) ---
elif menu_option == "Game Predictions":
    st.header("📈 Moneyline, Spread & Over/Under Predictions")
    
    selected_games = st.multiselect("Select Games for Predictions:", todays_games + tomorrows_games)
    
    if len(selected_games) == 0:
        st.warning("⚠️ Please select at least one game.")
    else:
        if st.button("Get Game Predictions"):
            predictions = fetch_game_predictions(selected_games)
            st.write(predictions)

    # --- Sharp Money & Line Movement Tracker ---
    st.header("💰 Sharp Money & Line Movement Tracker")
    if len(selected_games) > 0 and st.button("Check Betting Trends"):
        sharp_trends = fetch_sharp_money_trends(selected_games)
        st.write(sharp_trends)
