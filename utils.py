import requests
import os
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from bs4 import BeautifulSoup
import streamlit as st
from nba_api.stats.endpoints import playergamelog, leaguedashteamstats, scoreboardv2
from nba_api.stats.static import players
from nba_api.stats.endpoints import commonplayerinfo

# API Keys
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# --- Cache Game Fetching for Performance ---
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_games_by_date(target_date):
    """Fetches NBA games scheduled for a given date using the NBA Scoreboard API."""
    formatted_date = target_date.strftime("%Y-%m-%d")  # Convert date to proper format
    
    try:
        # Get NBA scoreboard data for the selected date
        scoreboard = scoreboardv2.ScoreboardV2(game_date=formatted_date)
        games_df = scoreboard.get_data_frames()[0]

        # Extract game matchups
        if games_df.empty:
            return ["No games available"]

        game_list = [
            f"{row['GAMECODE'][:3]} vs {row['GAMECODE'][3:6]}"
            for _, row in games_df.iterrows()
        ]
        return game_list

    except Exception as e:
        return [f"Error fetching games: {str(e)}"]

# --- Cache Player List to Reduce API Calls ---
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_all_players():
    """Fetches and caches the list of all NBA players."""
    return players.get_players()

# --- Fetch Player Stats (With Optimized Calls) ---
@st.cache_data(ttl=600)  # Cache for 10 minutes
def fetch_player_data(player_name, trend_length):
    """ Fetches real-time player stats from NBA API with caching """

    # Get Cached Player List
