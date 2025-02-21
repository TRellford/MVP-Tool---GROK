import requests
from scipy.stats import norm
from datetime import datetime

player_positions = {}
team_cache = {}

def get_player_id(player_name):
    """Fetch player ID by name."""
    url = f"https://www.balldontlie.io/api/v1/players?search={player_name}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data['data']:
            return data['data'][0]['id']
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player ID: {e}")
        return None

def get_team_id(team_name):
    """Fetch team ID by name."""
    if not team_cache:
        url = "https://www.balldontlie.io/api/v1/teams"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            for team in data['data']:
                team_cache[team['full_name'].lower()] = team['id']
        except requests.exceptions.RequestException as e:
            print(f"Error fetching teams: {e}")
            return None
    return team_cache.get(team_name.lower())

def get_player_team_id(player_id):
    """Fetch the player's current team ID."""
    url = f"https://www.balldontlie.io/api/v1/players/{player_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data['team']['id']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player team: {e}")
        return None

def get_last_n_games_stats(player_id, last_n_games=10):
    """Fetch player's stats for the last N games."""
    url = f"https://www.balldontlie.io/api/v1/stats?player_ids[]={player_id}&per_page=100"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        stats = sorted(data['data'], key=lambda x: x['game']['date'], reverse=True)
        return stats[:last_n_games]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching stats: {e}")
        return []

def get_last_n_game_ids(team_id, last_n_games=5):
    """Fetch the last N game IDs for a team."""
    url = f"https://www.balldontlie.io/api/v1/games?team_ids[]={team_id}&per_page=100"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        games = sorted(data['data'], key=lambda x: x['date'], reverse=True)
        return [game['id'] for game in games[:last_n_games]]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching games: {e}")
        return []

def get_player_position(player_id):
    """Fetch or retrieve cached player position."""
    if player_id in player_positions:
        return player_positions[player_id]
    url = f"https://www.balldontlie.io/api/v1/players/{player_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        position = data['position']
        player_positions[player_id] = position
        return position
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player position: {e}")
        return None

def get_avg_stat_allowed(team_id, stat, position, last_n_games=5):
    """Calculate average stat allowed by a team to a position."""
    game_ids = get_last_n_game_ids(team_id, last_n_games)
    total_stat = 0
    count = 0
    for game_id in game_ids:
        game_url = f"https://www.balldontlie.io/api/v1/games/{game_id}"
        try:
            game_response = requests.get(game_url)
            game_response.raise_for_status()
            game_data = game_response.json()
            opponent_team_id = game_data['visitor_team']['id'] if team_id == game_data['home_team']['id'] else game_data['home_team']['id']
            stats_url = f"https://www.balldontlie.io/api/v1/stats?game_ids[]={game_id}&team_ids[]={opponent_team_id}&per_page=100"
            stats_response = requests.get(stats_url)
            stats_response.raise_for_status()
            stats_data = stats_response.json()
            for stat_entry in stats_data['data']:
                player_id = stat_entry['player']['id']
                player_pos = get_player_position(player_id)
                if player_pos and position in player_pos:
                    total_stat += stat_entry.get(stat, 0)
                    count += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for game {game_id}: {e}")
    return total_stat / count if count > 0 else None

def predict_player_prop(player_id, stat, prop_line, opponent_team_id, last_n_games=10):
    """Predict whether a player will go over/under a prop line."""
    stats = get_last_n_games_stats(player_id, last_n_games)
    if not stats:
        return None
    player_avg = sum([s[stat] for s in stats if stat in s]) / len(stats)
    position = get_player_position(player_id)
    if not position:
        return None
    position = position[0]  # Use first letter (e.g., 'F' from 'F-G')
    opponent_avg_allowed = get_avg_stat_allowed(opponent_team_id, stat, position)
    if opponent_avg_allowed is None:
        return None
    predicted_mean = (player_avg + opponent_avg_allowed) / 2
    stat_values = [s[stat] for s in stats if stat in s]
    if len(stat_values) < 2:
        return None
    std_dev = (sum([(x - player_avg)**2 for x in stat_values]) / (len(stat_values) - 1)) ** 0.5
    prob_over = 1 - norm.cdf(prop_line, loc=predicted_mean, scale=std_dev)
    prediction = "Over" if prob_over > 0.5 else "Under"
    confidence = prob_over * 100 if prob_over > 0.5 else (1 - prob_over) * 100
    return {
        "prediction": prediction,
        "confidence": confidence,
        "predicted_mean": predicted_mean,
        "std_dev": std_dev,
        "prop_line": prop_line
    }

def get_team_stats(team_id, last_n_games=10):
    """Fetch team stats for home and away games."""
    game_ids = get_last_n_game_ids(team_id, last_n_games)
    home_points = {'scored': [], 'allowed': []}
    away_points = {'scored': [], 'allowed': []}
    for game_id in game_ids:
        game_url = f"https://www.balldontlie.io/api/v1/games/{game_id}"
        try:
            game_response = requests.get(game_url)
            game_response.raise_for_status()
            game_data = game_response.json()
            if game_data['home_team']['id'] == team_id:
                home_points['scored'].append(game_data['home_team_score'])
                home_points['allowed'].append(game_data['visitor_team_score'])
            else:
                away_points['scored'].append(game_data['visitor_team_score'])
                away_points['allowed'].append(game_data['home_team_score'])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching game {game_id}: {e}")
    stats = {}
    if home_points['scored']:
        stats['home_avg_scored'] = sum(home_points['scored']) / len(home_points['scored'])
        stats['home_avg_allowed'] = sum(home_points['allowed']) / len(home_points['allowed'])
    if away_points['scored']:
        stats['away_avg_scored'] = sum(away_points['scored']) / len(away_points['scored'])
        stats['away_avg_allowed'] = sum(away_points['allowed']) / len(away_points['allowed'])
    return stats if stats else None

def predict_game_outcome(home_team_id, away_team_id, last_n_games=10):
    """Predict game outcomes (moneyline, spread, over/under)."""
    home_stats = get_team_stats(home_team_id, last_n_games)
    away_stats = get_team_stats(away_team_id, last_n_games)
    if not home_stats or not away_stats:
        return None
    home_avg_scored = home_stats.get('home_avg_scored', 0)
    home_avg_allowed = home_stats.get('home_avg_allowed', 0)
    away_avg_scored = away_stats.get('away_avg_scored', 0)
    away_avg_allowed = away_stats.get('away_avg_allowed', 0)
    predicted_home_points = (home_avg_scored + away_avg_allowed) / 2
    predicted_away_points = (away_avg_scored + home_avg_allowed) / 2
    predicted_total = predicted_home_points + predicted_away_points
    predicted_spread = predicted_home_points - predicted_away_points
    win_prob_home = max(0, min(1, 0.5 + (predicted_spread / 20)))  # Simplified model
    return {
        "predicted_home_points": predicted_home_points,
        "predicted_away_points": predicted_away_points,
        "predicted_total": predicted_total,
        "predicted_spread": predicted_spread,
        "win_prob_home": win_prob_home
    }

def get_games_by_date(date_str):
    """Fetch games for a specific date."""
    url = f"https://www.balldontlie.io/api/v1/games?dates[]={date_str}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['data']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching games: {e}")
        return []

def odds_to_implied_prob(odds):
    """Convert American odds to implied probability."""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return -odds / (-odds + 100)
​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​
