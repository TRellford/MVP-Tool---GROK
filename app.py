import utils
from datetime import datetime

def player_search():
    """Handle individual player prop predictions."""
    print("\n=== Player Prop Search ===")
    player_name = input("Enter player name (e.g., LeBron James): ").strip()
    player_id = utils.get_player_id(player_name)
    if not player_id:
        print("Player not found.")
        return

    prop_options = {'points': 'pts', 'assists': 'ast', 'rebounds': 'reb', '3pt made': 'fg3m'}
    prop_selection = input("Select prop (Points, Assists, Rebounds, 3PT Made, or All): ").lower()
    if prop_selection not in prop_options and prop_selection != 'all':
        print("Invalid prop selection.")
        return

    confidence_filter = float(input("Enter confidence score filter (e.g., 80 for 80%+): "))
    trend_period = int(input("Enter trend period (5, 10, or 15 games): "))
    opponent_team_name = input("Enter opponent team name (e.g., Boston Celtics): ").strip()
    opponent_team_id = utils.get_team_id(opponent_team_name)
    if not opponent_team_id:
        print("Opponent team not found.")
        return

    props = prop_options.values() if prop_selection == 'all' else [prop_options[prop_selection]]
    for prop in props:
        prop_line = float(input(f"Enter prop line for {prop} (e.g., 25.5): "))
        prediction = utils.predict_player_prop(player_id, prop, prop_line, opponent_team_id, trend_period)
        if prediction and prediction['confidence'] >= confidence_filter:
            print(f"\nPlayer: {player_name}")
            print(f"Prop: {prop}")
            print(f"Prediction: {prediction['prediction']} {prop_line}")
            print(f"Confidence Score: {prediction['confidence']:.2f}%")
            stats = utils.get_last_n_games_stats(player_id, trend_period)
            avg = sum([s[prop] for s in stats if prop in s]) / len(stats)
            print(f"Insight: Averaged {avg:.1f} {prop} over last {trend_period} games.")
            opp_avg = utils.get_avg_stat_allowed(opponent_team_id, prop, utils.get_player_position(player_id)[0])
            print(f"Opponent Insight: Allows {opp_avg:.1f} {prop} to {utils.get_player_position(player_id)}s on average.")
            edge = prediction['predicted_mean'] - prop_line if prediction['prediction'] == 'Over' else prop_line - prediction['predicted_mean']
            if edge > 0:
                print(f"Edge Detector: 🔥 {edge:.1f}-point edge detected.")
        else:
            print(f"No prediction meets the confidence filter for {prop}.")

def multi_game_props():
    """Handle multi-game prop selections for parlays."""
    print("\n=== Multi-Game Prop Selection ===")
    date_str = input("Enter date for games (YYYY-MM-DD, e.g., 2023-11-01): ").strip()
    games = utils.get_games_by_date(date_str)
    if not games:
        print("No games found for that date.")
        return

    print("Available games:")
    for i, game in enumerate(games):
        print(f"{i+1}. {game['home_team']['full_name']} vs. {game['visitor_team']['full_name']}")
    selected_indices = input("Enter game numbers (comma-separated, e.g., 1,2,3): ").split(',')
    selected_games = [games[int(i.strip()) - 1] for i in selected_indices if i.strip().isdigit()]

    confidence_filter = float(input("Enter confidence score filter (e.g., 75 for 75%+): "))
    prop_count = 0
    predictions = []

    for game in selected_games:
        home_team_id = game['home_team']['id']
        away_team_id = game['visitor_team']['id']
        teams = {home_team_id: game['home_team']['full_name'], away_team_id: game['visitor_team']['full_name']}
        print(f"\nGame: {game['home_team']['full_name']} vs. {game['visitor_team']['full_name']}")
        while prop_count < 8:
            player_name = input("Enter player name (or 'done' to finish this game): ").strip()
            if player_name.lower() == 'done':
                break
            player_id = utils.get_player_id(player_name)
            if not player_id or utils.get_player_team_id(player_id) not in teams:
                print("Player not found or not in this game.")
                continue
            prop = input("Select prop (Points, Assists, Rebounds, 3PT Made): ").lower()
            prop_map = {'points': 'pts', 'assists': 'ast', 'rebounds': 'reb', '3pt made': 'fg3m'}
            if prop not in prop_map:
                print("Invalid prop.")
                continue
            prop_line = float(input(f"Enter prop line for {prop}: "))
            opponent_team_id = home_team_id if utils.get_player_team_id(player_id) == away_team_id else away_team_id
            pred = utils.predict_player_prop(player_id, prop_map[prop], prop_line, opponent_team_id)
            if pred and pred['confidence'] >= confidence_filter:
                predictions.append({
                    'player': player_name,
                    'prop': prop_map[prop],
                    'prediction': pred,
                    'game': f"{game['home_team']['full_name']} vs. {game['visitor_team']['full_name']}",
                    'trend': utils.get_last_n_games_stats(player_id, 5)
                })
                prop_count += 1
            if prop_count >= 8:
                print("Maximum of 8 props reached.")
                break

    if predictions:
        print("\n=== Multi-Game Prop Predictions ===")
        for p in predictions:
            avg = sum([s[p['prop']] for s in p['trend'] if p['prop'] in s]) / len(p['trend'])
            print(f"Game: {p['game']}")
            print(f"Player: {p['player']}")
            print(f"Prop: {p['prop']}")
            print(f"Prediction: {p['prediction']['prediction']} {p['prediction']['prop_line']}")
            print(f"Confidence Score: {p['prediction']['confidence']:.2f}%")
            print(f"5-Game Trend: Averaged {avg:.1f} {p['prop']}")
            edge = p['prediction']['predicted_mean'] - p['prediction']['prop_line'] if p['prediction']['prediction'] == 'Over' else p['prediction']['prop_line'] - p['prediction']['predicted_mean']
            if edge > 0:
                print(f"Edge Detector: 🔥 {edge:.1f}-point edge detected.")
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
        print(f"{i+1}. {game['home_team']['full_name']} vs. {game['visitor_team']['full_name']}")
    game_choice = int(input("Enter game number: ")) - 1
    game = games[game_choice]
    home_team_id = game['home_team']['id']
    away_team_id = game['visitor_team']['id']

    bet_type = input("Select bet type (Moneyline, Spread, Over/Under, or All): ").lower()
    if bet_type not in ['moneyline', 'spread', 'over/under', 'all']:
        print("Invalid bet type.")
        return

    prediction = utils.predict_game_outcome(home_team_id, away_team_id)
    if not prediction:
        print("Unable to make prediction.")
        return

    print(f"\nGame: {game['home_team']['full_name']} vs. {game['visitor_team']['full_name']}")
    if bet_type in ['moneyline', 'all']:
        print(f"Moneyline: {game['home_team']['full_name']} to win (Win Probability: {prediction['win_prob_home']*100:.2f}%)")
        odds = float(input("Enter sportsbook moneyline odds for home team (e.g., -150): "))
        implied_prob = utils.odds_to_implied_prob(odds)
        edge = prediction['win_prob_home'] - implied_prob
        if edge > 0:
            print(f"Edge Detector: 🔥 {edge*100:.2f}% edge detected.")
    if bet_type in ['spread', 'all']:
        print(f"Spread: {game['home_team']['full_name']} {prediction['predicted_spread']:.1f}")
        sportsbook_spread = float(input("Enter sportsbook spread (e.g., -3.5): "))
        edge = prediction['predicted_spread'] - sportsbook_spread if prediction['predicted_spread'] > 0 else sportsbook_spread - prediction['predicted_spread']
        if edge > 0:
            print(f"Edge Detector: 🔥 {edge:.1f}-point edge detected.")
    if bet_type in ['over/under', 'all']:
        print(f"Over/Under: {prediction['predicted_total']:.1f}")
        sportsbook_total = float(input("Enter sportsbook total (e.g., 225.5): "))
        edge = prediction['predicted_total'] - sportsbook_total
        if edge > 0:
            print(f"Edge Detector: 🔥 {edge:.1f}-point edge for Over.")
        elif edge < 0:
            print(f"Edge Detector: 🔥 {-edge:.1f}-point edge for Under.")

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
