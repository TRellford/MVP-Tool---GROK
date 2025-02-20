import requests
import streamlit as st

def get_api_key():
    """Retrieve the API key from Streamlit secrets.
    
    Raises:
        KeyError: If the API key is not found in Streamlit secrets.
    """
    try:
        return st.secrets["ODDS_API_KEY"]
    except KeyError:
        st.error("Please add your Odds API key to Streamlit secrets (e.g., in secrets.toml or Streamlit Cloud settings).")
        st.stop()

@st.cache_data(ttl=60)  # Cache for 60 seconds to respect API rate limits
def fetch_games(date):
    """Fetch NBA games for a given date from The Odds API.
    
    Args:
        date (str): The date to fetch games for, either 'today' or 'tomorrow'.
        
    Returns:
        list: A list of game strings in the format 'Home Team vs Away Team'.
    """
    api_key = get_api_key()
    sport = 'basketball_nba'
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={api_key}®ions=us&markets=h2h"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        games = [f"{event['home_team']} vs {event['away_team']}" for event in data]
        return games
    else:
        st.error(f"Failed to fetch games: HTTP {response.status_code}")
        return []

@st.cache_data(ttl=30)  # Cache for 30 seconds since odds update frequently
def fetch_odds(game):
    """Fetch the best available odds for a selected game from The Odds API.
    
    Args:
        game (str): The selected game in the format 'Home Team vs Away Team'.
        
    Returns:
        dict: A dictionary containing the best Moneyline, Spread, and Over/Under odds.
    """
    api_key = get_api_key()
    sport = 'basketball_nba'
    regions = 'us'
    markets = 'h2h,spreads,totals'  # Moneyline, Spread, Over/Under
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={api_key}®ions={regions}&markets={markets}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for event in data:
            if f"{event['home_team']} vs {event['away_team']}" == game:
                bookmakers = event['bookmakers']
                # Find best Moneyline (highest odds for home team)
                best_ml = max(bookmakers, key=lambda b: b['markets'][0]['outcomes'][0]['price'])
                # Find best Spread (lowest point for favorite, assuming home team is favorite if point < 0)
                best_spread = min(bookmakers, key=lambda b: b['markets'][1]['outcomes'][0]['point'] if b['markets'][1]['outcomes'][0]['name'] == event['home_team'] else float('inf'))
                # Find best Over/Under (lowest total points)
                best_ou = min(bookmakers, key=lambda b: b['markets'][2]['outcomes'][0]['point'])
                return {
                    'moneyline': {'book': best_ml['title'], 'odds': best_ml['markets'][0]['outcomes'][0]['price']},
                    'spread': {'book': best_spread['title'], 'point': best_spread['markets'][1]['outcomes'][0]['point'], 'odds': best_spread['markets'][1]['outcomes'][0]['price']},
                    'over_under': {'book': best_ou['title'], 'total': best_ou['markets'][2]['outcomes'][0]['point'], 'odds': best_ou['markets'][2]['outcomes'][0]['price']}
                }
        return {"error": "Game not found in API response"}
    else:
        return {"error": f"API request failed with status {response.status_code}"}

@st.cache_data(ttl=30)  # Cache for 30 seconds since props update frequently
def fetch_player_props(game):
    """Fetch player props for the selected game from The Odds API.
    
    Args:
        game (str): The selected game in the format 'Home Team vs Away Team'.
        
    Returns:
        list: A list of player prop dictionaries.
    """
    api_key = get_api_key()
    sport = 'basketball_nba'
    regions = 'us'
    markets = 'player_points,player_rebounds,player_assists,player_threes'  # Example player prop markets
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={api_key}®ions={regions}&markets={markets}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        props = []
        for event in data:
            if f"{event['home_team']} vs {event['away_team']}" == game:
                for bookmaker in event['bookmakers']:
                    for market in bookmaker['markets']:
                        for outcome in market['outcomes']:
                            props.append({
                                'player': outcome['description'],
                                'prop_type': market['key'].replace('player_', ''),  # e.g., 'points'
                                'value': outcome.get('point', 'N/A'),  # Some props may not have a point value
                                'odds': outcome['price'],
                                'bookmaker': bookmaker['title']
                            })
        return props if props else [{"error": "No player props available for this game"}]
    else:
        return [{"error": f"API request failed with status {response.status_code}"}]
