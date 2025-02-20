import streamlit as st
from utils import fetch_games, fetch_odds, fetch_player_props
import pandas as pd
from datetime import datetime, timedelta

# --- Streamlit App ---

st.title("NBA Betting Analysis Tool")
st.write("Select a game from the sidebar to view live odds and player props powered by The Odds API.")

# Sidebar for game selection
st.sidebar.title("Game Selection")
date_option = st.sidebar.radio("Select Date", ["Today", "Tomorrow"])
# Note: The Odds API fetches all available games; date filtering could be added with commence_time
games = fetch_games(date_option.lower())
selected_game = st.sidebar.selectbox("Select Game", games)

# Main content
if selected_game:
    # Display live odds
    st.header("Best Available Odds")
    odds = fetch_odds(selected_game)
    if "error" in odds:
        st.error(odds["error"])
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Moneyline", f"{odds['moneyline']['odds']} ({odds['moneyline']['book']})")
        with col2:
            st.metric("Spread", f"{odds['spread']['point']} ({odds['spread']['book']}, {odds['spread']['odds']})")
        with col3:
            st.metric("Over/Under", f"{odds['over_under']['total']} ({odds['over_under']['book']}, {odds['over_under']['odds']})")

    # Display live player props
    st.header("Player Props")
    props = fetch_player_props(selected_game)
    if props and "error" not in props[0]:
        df = pd.DataFrame(props)
        st.dataframe(df[['player', 'prop_type', 'value', 'odds', 'bookmaker']], use_container_width=True)
    else:
        st.error(props[0]["error"])

else:
    st.write("Please select a game from the sidebar to view live data.")

# Sidebar footer
st.sidebar.markdown("---")
st.sidebar.write("This app uses live data from The Odds API. Ensure your API key is configured in Streamlit secrets.")
