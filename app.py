import streamlit as st
import plotly.express as px
from utils import (get_player_id, fetch_game_logs, get_last_10_games, 
                  calculate_averages, fetch_nba_games, fetch_odds, 
                  calculate_betting_edge)

# --- Main Streamlit App ---

def main():
    st.title("NBA Betting Prediction Tool")
    st.write("Analyze player stats, game odds, and identify betting edges!")

    # Sidebar for game selection
    st.sidebar.header("Game Selection")
    today_or_tomorrow = st.sidebar.radio("Select Day", ["Today", "Tomorrow"])
    games = fetch_nba_games(today=True if today_or_tomorrow == "Today" else False)
    selected_game = st.sidebar.selectbox("Choose a Game", games) if games else st.sidebar.write("No games found.")

    # Multi-player selection
    st.header("Player Analysis")
    player_names = st.multiselect("Select Players (e.g., LeBron James)", 
                                  ["LeBron James", "Stephen Curry", "Kevin Durant"], 
                                  default=["LeBron James"])
    
    if st.button("Analyze"):
        if not selected_game:
            st.error("Please select a game.")
            return
        
        with st.spinner("Fetching data..."):
            # Fetch odds for selected game
            odds = fetch_odds(selected_game)
            if not odds:
                st.warning("No odds available for this game.")
            
            # Process each selected player
            for player_name in player_names:
                st.subheader(f"Analysis for {player_name}")
                
                # Get player ID and game logs
                player_id = get_player_id(player_name)
                if not player_id:
                    st.error(f"Player '{player_name}' not found.")
                    continue
                
                game_logs = fetch_game_logs(player_id)
                if not game_logs:
                    st.error(f"Failed to fetch game logs for {player_name}.")
                    continue
                
                last_10 = get_last_10_games(game_logs)
                if not last_10:
                    continue
                
                # Calculate averages
                averages = calculate_averages(last_10)
                if averages:
                    # Display averages
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Points: **{averages['Points']:.2f}**")
                        st.write(f"Rebounds: **{averages['Rebounds']:.2f}**")
                    with col2:
                        st.write(f"Assists: **{averages['Assists']:.2f}**")
                        st.write(f"Minutes: **{averages['Minutes']:.2f}**")

                    # Betting edge calculation
                    if odds:
                        for market in odds:
                            if market['key'] == 'totals' and 'Points' in market['outcomes'][0]['name']:
                                line = market['outcomes'][0]['point']
                                price = market['outcomes'][0]['price']
                                ev = calculate_betting_edge(averages['Points'], line, price)
                                st.write(f"Points Over {line} (Odds: {price}): EV = {ev:.2f}")
                                if ev > 0:
                                    st.success(f"Betting Edge Detected: Over {line} Points")

                    # Visualization
                    fig = px.line(last_10, x="GAME_DATE", y="PTS", title=f"{player_name} Points Trend (Last {len(last_10)} Games)")
                    st.plotly_chart(fig)

                # Raw data toggle
                if st.checkbox(f"Show {player_name}'s Raw Game Logs"):
                    st.write(last_10[['GAME_DATE', 'MATCHUP', 'PTS', 'REB', 'AST', 'MIN']])

if __name__ == "__main__":
    main()
