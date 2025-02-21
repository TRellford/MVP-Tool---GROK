import streamlit as st
import utils
import requests

st.title("NBA Betting Prediction System")

BALL_DONT_LIE_BASE_URL = "https://www.balldontlie.io/api/v1"

player_name = st.text_input("Enter player name to test API")

if st.button("Test API"):
    url = f"{BALL_DONT_LIE_BASE_URL}/players?search={player_name}"
    response = requests.get(url)
    
    st.write(f"Status Code: {response.status_code}")
    st.write("Raw Response:")
    st.code(response.text)

    try:
        data = response.json()
        st.write("JSON Response:")
        st.json(data)
    except:
        st.error("Response is not valid JSON!")


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

    prop_options = {'Points': 'player_points', 'Assists': 'player_assists', 'Rebounds': 'player_rebounds', '3PT Made': 'player_threes'}
    prop_selection = st.selectbox("Select prop", ["All"] + list(prop_options.keys()))
    confidence_filter = st.number_input("Confidence score filter (e.g., 80 for 80%+)", min_value=0.0, max_value=100.0, value=80.0)
    trend_period = st.selectbox("Trend period (games)", [5, 10, 15])

    if st.button("Predict"):
        props = prop_options.values() if prop_selection == 'All' else [prop_options[prop_selection]]
        for prop in props:
            prop_line = st.number_input(f"Enter prop line for {prop.split('_')[1]} (e.g., 25.5)", value=25.5, key=f"{player_name}_{prop}")
            prediction = utils.predict_player_prop(player_name, prop, prop_line, selected_game, trend_period)
            if prediction and "confidence" in prediction and prediction['confidence'] >= confidence_filter:
                st.write(f"**Player:** {player_name}")
                st.write(f"**Prediction:** {prediction['prediction']} {prop_line} ({prediction['odds']})")
                st.write(f"**Confidence Score:** {prediction['confidence']:.2f}%")
                if prediction['edge'] > 0:
                    st.write(f"**Edge Detector:** 🔥 {prediction['edge']:.1f}-point edge detected.")
                st.write(f"**Risk Level:** {prediction['risk_level']}")
            else:
                st.write(f"No prediction meets confidence filter for {prop}.")

def multi_game_prop_selection():
    st.subheader("Multi-Game Prop Selection")

    games_today = utils.get_games_by_date(st.session_state.get("selected_date", "today"))
    if not games_today:
        st.write("No games found for today.")
        return

    game_options = [f"{game['home_team']} vs {game['away_team']} ({game['commence_time']})" for game in games_today]
    selected_games = st.multiselect("Select games", game_options)

    prop_options = {'Points': 'player_points', 'Assists': 'player_assists', 'Rebounds': 'player_rebounds', '3PT Made': 'player_threes'}
    selected_props = st.multiselect("Select props", list(prop_options.keys()))

    confidence_filter = st.number_input("Confidence score filter (e.g., 80 for 80%+)", min_value=0.0, max_value=100.0, value=80.0)
    trend_period = st.selectbox("Trend period (games)", [5, 10, 15])

    if st.button("Predict"):
        for game_option in selected_games:
            game_idx = game_options.index(game_option)
            game = games_today[game_idx]
            st.write(f"### Predictions for {game['home_team']} vs {game['away_team']}")

            for prop in selected_props:
                st.write(f"#### {prop}")
                player_names = utils.get_players_from_game(game['id'])  # Fetch players from the game
                for player in player_names:
                    prop_key = prop_options[prop]
                    prop_line = st.number_input(f"Enter line for {player}'s {prop} (e.g., 25.5)", value=25.5, key=f"{game['id']}_{player}_{prop}")

                    prediction = utils.predict_player_prop(player, prop_key, prop_line, game, trend_period)
                    if prediction and "confidence" in prediction and prediction['confidence'] >= confidence_filter:
                        st.write(f"**Player:** {player}")
                        st.write(f"**Prediction:** {prediction['prediction']} {prop_line} ({prediction['odds']})")
                        st.write(f"**Confidence Score:** {prediction['confidence']:.2f}%")
                        if prediction['edge'] > 0:
                            st.write(f"**Edge Detector:** 🔥 {prediction['edge']:.1f}-point edge detected.")
                        st.write(f"**Risk Level:** {prediction['risk_level']}")
                    else:
                        st.write(f"No prediction meets confidence filter for {player} - {prop}.")

def game_predictions():
    st.subheader("Game Predictions")

    games_today = utils.get_games_by_date(st.session_state.get("selected_date", "today"))
    if not games_today:
        st.write("No games found for today.")
        return

    game_options = [f"{game['home_team']} vs {game['away_team']} ({game['commence_time']})" for game in games_today]
    selected_game_str = st.selectbox("Select a game", game_options)

    game_idx = game_options.index(selected_game_str)
    selected_game = games_today[game_idx]

    if st.button("Predict"):
        predictions = utils.predict_game_outcome(selected_game)

        if predictions:
            st.write(f"### Predictions for {selected_game['home_team']} vs {selected_game['away_team']}")
            
            # Moneyline Prediction
            moneyline = predictions["moneyline"]
            st.write(f"#### Moneyline: **{moneyline['team']}** ({moneyline['odds']})")
            st.write(f"**Win Probability:** {moneyline['win_prob']:.2f}%")
            if moneyline['edge'] > 0:
                st.write(f"**Betting Edge:** 🔥 {moneyline['edge']:.2f} edge detected.")

            # Spread Prediction
            spread = predictions["spread"]
            st.write(f"#### Spread: **{spread['line']}** ({spread['odds']})")
            st.write(f"**Edge:** {spread['edge']:.2f}")

            # Over/Under Prediction
            over_under = predictions["over_under"]
            st.write(f"#### Over/Under: **{over_under['prediction']} {over_under['line']}** ({over_under['odds']})")
            st.write(f"**Edge:** {over_under['edge']:.2f}")

        else:
            st.write("No predictions available for this game.")

def main():
    menu = ["Player Search", "Multi-Game Prop Selection", "Game Predictions"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Player Search":
        player_search()
    elif choice == "Multi-Game Prop Selection":
        multi_game_prop_selection()
    elif choice == "Game Predictions":
        game_predictions()

main()
