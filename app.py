import streamlit as st
from nba_api.stats.endpoints import playergamelog, leaguegamefinder
from nba_api.stats.static import players
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px

# --- Constants and Configuration ---
ODDS_API_KEY = 06f33a81a9869429c717a7ac27b205ae
SPORT = "basketball_nba"
SEASON = "2024-25"

# --- Helper Functions ---

def get_player_id(player_name):
    player_dict = players.find_players_by_full_name(player_name)
    return player_dict[0]['id'] if player_dict else None

def fetch_game_logs(player_id):
    try:
        game_log = playergamelog.PlayerGameLog(player_id=player_id, season=SEASON)
        return game_log.get_data_frames()[0]
    except Exception as e:
        st.error(f"Error fetching game logs: {e}")
        return None

def get_last_10_games(df):
    if df is None or len(df) == 0:
        return None
    return df.head(10) if len(df) >= 10 else df

def calculate_averages(df):
    if df is None:
        return None
    return {
        'Points': df['PTS'].mean(),
        'Rebounds': df['REB'].mean(),
        'Assists': df['AST'].mean(),
        'Minutes': df['MIN'].mean()
    }

def fetch_nba_games(today=True):
    """Fetch games for today or tomorrow."""
    game_finder = leaguegamefinder.LeagueGameFinder(league_id_nullable='00', season_nullable=SEASON)
    games_df = game_finder.get_data_frames()[0]
    date_str = datetime.now().strftime("%Y-%m-%d") if today else (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    return games_df[games_df['GAME_DATE'] == date_str]['MATCHUP'].tolist()

def fetch_odds(game_matchup):
    """Fetch odds for a specific game from The Odds API."""
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/?apiKey={ODDS_API_KEY}&regions=us&markets=h2h,spreads,totals"
    response = requests.get(url)
    if response.status_code == 200:
        odds_data = response.json()
        for game in odds_data:
            if game_matchup in f"{game['home_team']} vs. {game['away_team']}" or game_matchup in f"{game['away_team']} @ {game['home_team']}":
                return game['bookmakers'][0]['markets']  # Use first bookmaker (e.g., DraftKings)
    return None

def calculate_betting_edge(avg_stat, odds_line, odds_price):
    """Simple EV calculation: Compare avg stat to odds line."""
    # Convert American odds to implied probability
    if odds_price > 0:
        implied_prob = 100 / (odds_price + 100)
    else:
        implied_prob = -odds_price / (-odds_price + 100)
    
    # Historical probability ( simplistic: avg stat > line = 100% hit rate if true)
    hit_rate = 1 if avg_stat > odds_line else 0
    ev = (hit_rate * (odds_price / 100 if odds_price > 0 else 1)) - ((1 - hit_rate) * 1)
    return ev

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

                    # Betting edge calculation (example: points total)
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
