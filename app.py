import streamlit as st
import datetime
from utils import (
    get_games_by_date, fetch_player_data, fetch_best_props, 
    fetch_game_predictions, fetch_sgp_builder, fetch_sharp_money_trends
)

st.set_page_config(page_title="NBA Betting AI", layout="wide")

# --- Get Today's & Tomorrow's Dates ---
today = datetime.datetime.today()
tomorrow = today + datetime.timedelta(days=1)

# --- Fetch Games ---
todays_games = get_games_by_date(today)
tomorrows_games = get_games_by_date(tomorrow)

# --- Sidebar Navigation ---
st.sidebar.title("🔍 Navigation")
menu_option = st.sidebar.radio("Select a Section:", ["Player Search", "SGP Builder", "SGP+ Builder", "Game Predictions"])

# --- Game Selection ---
st.sidebar.header("📅 Select NBA Games")
selected_date = st.sidebar.radio("Choose Game Date:", ["Today's Games", "Tomorrow's Games"])
game_selection = st.sidebar.selectbox(
    "Select a Game:",
    todays_games if selected_date == "Today's Games" else tomorrows_games
)

st.sidebar.success(f"📅 Selected Game: {game_selection}")

# --- Section 1: Player Search ---
if menu_option == "Player Search":
    st.header("🔍 Player Performance & Prop Bets")
    player_name = st.text_input("Enter Player Name (e.g., Kevin Durant)")
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
                st.dataframe(stats_df)

    # Best Player Prop
    st.header("🔥 AI Best Player Props")
    if st.button("Find Best Player Prop"):
        best_prop = fetch_best_props(player_name, trend_length)
        if "error" in best_prop:
            st.error(best_prop["error"])
        else:
            st.success(f"🔥 Best Bet for {player_name}: **{best_prop['best_prop']}**")
            st.write(f"📊 **Average {best_prop['best_prop']}:** {best_prop['average_stat']} per game")
            st.write(f"🚨 **Weakest Defensive Teams Against {best_prop['best_prop']}:** {', '.join(best_prop['weak_defensive_teams'])}")

# --- Section 2: Same Game Parlay (SGP) Builder ---
elif menu_option == "SGP Builder":
    st.header("🎯 Same Game Parlay (SGP) Builder")
    sgp_props = st.multiselect("Select Props for SGP:", ["Points", "Assists", "Rebounds", "3PT Made"])
    if st.button("Generate SGP"):
        sgp_result = fetch_sgp_builder(game_selection, sgp_props)
        st.write(sgp_result)

# --- Section 3: SGP+ Builder (Multi-Game Parlay) ---
elif menu_option == "SGP+ Builder":
    st.header("🔥 Multi-Game Parlay (SGP+) Builder")

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
    if st.button("Get Game Predictions"):
        predictions = fetch_game_predictions(game_selection)
        st.write(predictions)

    # --- Sharp Money & Line Movement Tracker ---
    st.header("💰 Sharp Money & Line Movement Tracker")
    if st.button("Check Betting Trends"):
        sharp_trends = fetch_sharp_money_trends(game_selection)
        st.write(sharp_trends)
