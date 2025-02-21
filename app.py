import utils
from datetime import datetime

def player_search():
    """Handle individual player prop predictions."""
    print("\n=== Player Prop Search ===")
    player_name = input("Enter player name (e.g., LeBron James): ").strip()
    player_games = utils.find_player_games(player_name)
    if not player_games:
        print("No upcoming games found for this player.")
        return

    print("Upcoming games for", player_name + ":")
    for i, game in enumerate(player_games):
        print(f"{i+1}. {game['home_team']} vs {game['away_team']} ({game['commence_time']})")
    game_idx = int(input("Select game number: ")) - 1
    selected_game = player_games[game_idx]

    prop_options = {'points': 'player_points', 'assists': 'player_assists', 'rebounds': 'player_rebounds', '3pt made': 'player_threes'}
    prop_selection = input("Select prop (Points, Assists, Rebounds, 3PT Made, or All): ").lower()
    if prop_selection not in prop_options and prop_selection != 'all':
        print("Invalid prop selection.")
        return

    confidence_filter = float(input("Enter confidence score filter (e.g., 80 for 80%+): "))
    trend_period = int(input("Enter trend period (5, 10, or 15 games): "))

    props = prop_options.values() if prop_selection == 'all' else [prop_options[prop_selection]]
    for prop in props:
        prop_line = float(input(f"Enter prop line for {prop.split('_')[1]} (e.g., 25.5): "))
        prediction = utils.predict_player_prop(player_name, prop, prop_line, selected_game, trend_period)
        if prediction and prediction['confidence'] >= confidence_filter:
            print(f"\nPlayer: {player_name}")
            print(f"Prop: {prop.split('_')[1]}")
            print(f"Prediction: {prediction['prediction']} {prop_line} ({prediction['odds']})")
            print(f"Confidence Score: {prediction['confidence']:.2f}%")
            print(f"Insight: {prediction['insight']}")
            if prediction['edge'] > 0:
                print(f"Edge Detector: 🔥 {prediction['edge']:.1f}-point edge detected.")
            print(f"Risk Level: {prediction['risk_level']}")
        else:
            print(f"No prediction meets the confidence filter for {prop}.")

def multi_game_props():
    """Handle multi-game prop selections for parlays."""
    print("\n=== Multi-Game Prop Selection ===")
    date_str = input("Enter date for games (YYYY-MM-DD, e.g., 2025-02-21): ").strip()
    games = utils.get_games_by_date(date_str)
    if not games:
        print("No games found for that date.")
        return

    print("Available games:")
    for i, game in enumerate(games):
        print(f"{i+1}. {game['home_team']} vs {game['away_team']} ({game['commence_time']})")
    selected_indices = input("Enter game numbers (comma-separated, e.g., 1,2,3): ").split(',')
    selected_games = [games[int(i.strip()) - 1] for i in selected_indices if i.strip().isdigit()]

    confidence_filter = float(input("Enter confidence score filter (e.g., 75 for 75%+): "))
    prop_count = 0
    predictions = []

    for game in selected_games:
        print(f"\nGame: {game['home_team']} vs {game['away_team']}")
        while prop_count < 8:
            player_name = input("Enter player name (or 'done' to finish this game): ").strip()
            if player_name.lower() == 'done':
                break
            if not utils.is_player_in_game(player_name, game):
                print("Player not found in this game.")
                continue
            prop = input("Select prop (Points, Assists, Rebounds, 3PT Made): ").lower()
            prop_map = {'points': 'player_points', 'assists': 'player_assists', 'rebounds': 'player_rebounds', '3pt made': 'player_threes'}
            if prop not in prop_map:
                print("Invalid prop.")
                continue
            prop_line = float(input(f"Enter prop line for {prop}: "))
            pred = utils.predict_player_prop(player_name, prop_map[prop], prop_line, game)
            if pred and pred['confidence'] >= confidence_filter:
                predictions.append({
                    'player': player_name,
                    'prop': prop_map[prop],
                    'prediction': pred,
                    'game': f"{game['home_team']} vs {game['away_team']}"
                })
                prop_count += 1
            if prop_count >= 8:
                print("Maximum of 8 props reached.")
                break

    if predictions:
        print("\n=== Multi-Game Prop Predictions ===")
        for p in predictions:
            print(f"Game: {p['game']}")
            print(f"Player: {p['player']}")
            print(f"Prop: {p['prop'].split('_')[1]}")
            print(f"Prediction: {p['prediction']['prediction']} {p['prediction']['prop_line']} ({p['prediction']['odds']})")
            print(f"Confidence Score: {p['prediction']['confidence']:.2f}%")
            print(f"Insight: {p['prediction']['insight']}")
            if p['prediction']['edge'] > 0:
                print(f"Edge Detector: 🔥 {p['prediction']['edge']:.1f}-point edge detected.")
            print()

def game_predictions():
    """Handle game outcome predictions."""
    print("\n=== Game Predictions ===")
    date_str = input("Enter date for games (YYYY-MM-DD): ").strip()
    games = utils.get_games_by_date(date_str)
    if not games:
        print("No games found for that date.")
        return

    print("Select a game:")
    for i, game in enumerate(games):
        print(f"{i+1}. {game['home_team']} vs {game['away_team']} ({game['commence_time']})")
    game_choice = int(input("Enter game number: ")) - 1
    game = games[game_choice]

    bet_type = input("Select bet type (Moneyline, Spread, Over/Under, or All): ").lower()
    if bet_type not in ['moneyline', 'spread', 'over/under', 'all']:
        print("Invalid bet type.")
        return

    prediction = utils.predict_game_outcome(game)
    if not prediction:
        print("Unable to make prediction.")
        return

    print(f"\nGame: {game['home_team']} vs {game['away_team']}")
    if bet_type in ['moneyline', 'all']:
        print(f"Moneyline: {prediction['moneyline']['team']} to win (Win Probability: {prediction['moneyline']['win_prob']*100:.2f}%)")
        print(f"Bookmaker Odds: {prediction['moneyline']['odds']}")
        edge = prediction['moneyline']['edge']
        if edge > 0:
            print(f"Edge Detector: 🔥 {edge*100:.2f}% edge detected.")
    if bet_type in ['spread', 'all']:
        print(f"Spread: {game['home_team']} {prediction['spread']['line']:.1f} ({prediction['spread']['odds']})")
        edge = prediction['spread']['edge']
        if edge > 0:
            print(f"Edge Detector: 🔥 {edge:.1f}-point edge detected.")
    if bet_type in ['over/under', 'all']:
        print(f"Over/Under: {prediction['over_under']['prediction']} {prediction['over_under']['line']:.1f} ({prediction['over_under']['odds']})")
        edge = prediction['over_under']['edge']
        if edge > 0:
            print(f"Edge Detector: 🔥 {edge:.1f}-point edge for {prediction['over_under']['prediction']}.")

def main():
    """Main application loop."""
    while True:
        print("\n=== NBA Betting Prediction System ===")
        print("1. Player Search")
        print("2. Multi-Game Prop Selection")
        print("3. Game Predictions")
        print("4. Exit")
        choice = input("Enter 1, 2, 3, or 4: ").strip()
        if choice == '1':
            player_search()
        elif choice == '2':
            multi_game_props()
        elif choice == '3':
            game_predictions()
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​
