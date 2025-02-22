import streamlit as st
import matplotlib.pyplot as plt
from utils import fetch_player_data, fetch_best_props

st.set_page_config(page_title="NBA Betting AI", layout="wide")

st.title("📈 AI-Powered NBA Betting Predictions")

# --- Player Trend Analysis ---
st.header("🔍 Player Performance Insights")

player_name = st.text_input("Enter Player Name (e.g., Kevin Durant)")
trend_length = st.radio("Select Trend Length", [5, 10, 15])

if st.button("Generate Insights"):
    if not player_name:
        st.warning("Please enter a player name.")
    else:
        stats_df = fetch_player_data(player_name, trend_length)

        if "error" in stats_df:
            st.error(stats_df["error"])
        else:
            fig, ax = plt.subplots(figsize=(10, 5))

            ax.plot(stats_df["Game Date"], stats_df["Points"], marker="o", label="Points")
            ax.plot(stats_df["Game Date"], stats_df["Rebounds"], marker="s", label="Rebounds")
            ax.plot(stats_df["Game Date"], stats_df["Assists"], marker="^", label="Assists")

            ax.set_xlabel("Game Date")
            ax.set_ylabel("Stats")
            ax.set_title(f"{player_name} - Last {trend_length} Games")
            ax.legend()
            plt.xticks(rotation=45)

            st.pyplot(fig)

# --- Auto-Fetch Best Player Props ---
st.header("📊 Best Player Prop Bets Based on Matchups")

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
