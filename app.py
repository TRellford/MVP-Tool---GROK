import streamlit as st
import utils

st.title("NBA Betting Prediction System")

def player_search():
    st.subheader("Player Prop Search")
    player_name = st.text_input("Enter player name (e.g., LeBron James)")
    if not player_name:
        return

    player_games = utils.find_player_games(player_name)
    if not player_games:
        st.write("No upcoming games found for this player.")
        return

    st.write(f"Upcoming games for {player_name}:")
    game_options = [f"{game['home_team']} vs {game['away_team']} ({game['commence_time']})" for game in player_games]
    selected_game_str = st.selectbox("Select a game", game_options)
    game_idx = game_options.index(selected_game_str)
    selected_game = player_games[game_idx]

    prop_options = {'points': 'player_points', 'assists': 'player_assists', 'rebounds': 'player_rebounds', '3pt made': 'player_threes'}
    prop_selection = st.selectbox("Select prop", ["All"] + list(prop_options.keys())).lower()
    confidence_filter = st.number_input("Confidence score filter (e.g., 80 for 80%+)", min_value=0.0, max_value=100.0, value=80.0)
    trend_period = st.selectbox("Trend period (games)", [5, 10, 15])

    if st.button("Predict"):
        props = prop_options.values() if prop_selection == 'all' else [prop_options[prop_selection]]
        for prop in props:
            prop_line = st.number_input(f"Enter prop line for {prop.split('_')[1]} (e.g., 25.5)", value=25.5, key=prop)
            prediction = utils.predict_player_prop(player_name, prop, prop_line, selected_game, trend_period)
            if prediction and prediction['confidence'] >= confidence_filter:
                st.write(f"**Player:** {player_name}")
                st.write(f"**Prop:** {prop.split('_')[1]}")
                st.write(f"**Prediction:** {prediction['prediction']} {prop_line} ({prediction['odds']})")
                st.write(f"**Confidence Score:** {prediction['confidence']:.2f}%")
                st.write(f"**Insight:** {prediction['insight']}")
                if prediction['edge'] > 0:
                    st.write(f"**Edge Detector:** 🔥 {prediction['edge']:.1f}-point edge detected.")
                st.write(f"**Risk Level:** {prediction['risk_level']}")
            else:
                st.write(f"No prediction meets the confidence filter for {prop}.")

def main():
    menu = ["Player Search", "Multi-Game Prop Selection", "Game Predictions"]
    choice = st.sidebar.selectbox("Menu", menu)
    if choice == "Player Search":
        player_search()
    elif choice == "Multi-Game Prop Selection":
        st.write("Coming soon!")
    elif choice == "Game Predictions":
        st.write("Coming soon!")

if __name__ == "__main__":
    main()
​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​
