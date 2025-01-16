#This script creates a lineup, vs a pitcher
#The lineup can be edited manually vs the user

'''NEEDS'''
'''
- a team
- available batters
- an opposing pitcher


returns 9 players


How to Get a Team?
'''

import json
import pandas as pd
import teams
from player import Player
from strategies import Today
import requests
from lineupscraper import LineupScraper

def Go():
    todays_games = Today().get_game_ids()

    Lineups = LineupScraper()

    for game_id in todays_games:
        lineup_copy = Lineups
        url = f"http://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"
        response = requests.get(url)
        if response.status_code == 200:
            game_data = response.json()
            
            MetaData = game_data.get('metaData', {})
            GameData = game_data.get('gameData', {})
            LiveData = game_data.get('liveData', {})
            
            Teams = GameData.get('teams', {})
            away_code = Teams.get('away', {}).get('teamName')
            home_code = Teams.get('home', {}).get('teamName')
            
            BoxScore = LiveData.get('linescore', {}).get('boxscore', {})       
            HomeBoxScore = BoxScore.get('teams', {}).get('home', {})
            AwayBoxScore = BoxScore.get('teams', {}).get('away', {})
            

            away_batting_order = lineup_copy[lineup_copy['team'] == away_code]
            home_batting_order = lineup_copy[lineup_copy['team'] == home_code]

                
            print(away_batting_order)
            
            
            #For each batting order, process
            #Relative to opp starter, append the batters 'K%', or K% vs pitchers with vFA>95?
            
            
            #save batting order to files to be pulled
            dir = 'today_lineups'
        