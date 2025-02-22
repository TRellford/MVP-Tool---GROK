import streamlit as st
import datetime
from utils import get_games_by_date, fetch_player_data, fetch_best_props, fetch_game_predictions, fetch_sgp_builder

st.set_page_config(page_title="NBA Betting AI", layout="wide")

# --- Get Today's & Tomorrow's Dates ---
today = datetime.datetime.today()
tomorrow = today + datetime.timedelta(days=1)

# --- Fetch Games ---
todays_games = get_games_by_date(today)
tomorrows_games = get_games_by_date(tomorrow)

# --- UI ---
st.title("🏀 NBA Betting AI - Real-Time Game & Player Insights")

# --- Section 1: Select Game Date ---
st.header("📅 Select NBA Games")
selected_date = st.radio("Choose Game Date:", ["Today's Games", "Tomorrow's Games"])
game_selection = st.selectbox("Select a Game:", todays_games if selected_date == "Today's Games" else tomorrows_games)

st.success(f"📅 You selected: {game_selection}")

# --- Section 2: Player Search ---
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

# --- Section 3: Best Player Prop Bets ---
st.header("🔥 AI Best Player Props")
if st.button("Find Best Player Prop"):
    if not player_name:
        st.warning("Please enter a player name.")
    else:
        best_prop = fetch_best_props(player_name, trend_length)
        if "error" in best_prop:
            st.error(best_prop["error"])
        else:
            st.success(f"🔥 Best Bet for {player_name}: **{best_prop['best_prop']}**")
            st.write(f"📊 **Average {best_prop['best_prop']}:** {best_prop['average_stat']} per game")
            st.write(f"🚨 **Weakest Defensive Teams Against {best_prop['best_prop']}:** {', '.join(best_prop['weak_defensive_teams'])}")

# --- Section 4: Betting Predictions (ML, Spread, O/U) ---
st.header("📈 Moneyline, Spread & Over/Under Predictions")
if st.button("Get Game Predictions"):
    predictions = fetch_game_predictions(game_selection)
    st.write(predictions)

# --- Section 5: Same Game Parlay Builder ---
st.header("🎯 Same Game Parlay (SGP) Builder")
sgp_props = st.multiselect("Select Props for SGP:", ["Points", "Assists", "Rebounds", "3PT Made"])
if st.button("Generate SGP"):
    sgp_result = fetch_sgp_builder(game_selection, sgp_props)
    st.write(sgp_result)
