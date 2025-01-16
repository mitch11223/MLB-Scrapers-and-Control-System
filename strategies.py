import requests
import json
import csv
import unicodedata
from datetime import datetime
import pandas as pd
from node import Node


class Today:
    def __init__(self):
        self.todays_games = self.get_todays_games()
        with open('players/2024/pitcher_metadata.json', 'r') as f:
            self.pitchers = json.load(f)
            
    def get_todays_games(self):
        url = "http://statsapi.mlb.com/api/v1/schedule/games/?sportId=1"
        response = requests.get(url)
        if response.status_code == 200:
            response = response.json()
            with open('today/games/todays_games.json', 'w') as file:
                json.dump(response, file, indent=4)
            return response
        else:
            return {}

    def get_game_ids(self):
        """ Extract all game IDs from today's game data """
        game_ids = []
        try:
            games = self.todays_games.get('dates', [])[0].get('games', [])
            for game in games:
                game_ids.append(game.get('gamePk'))
        except IndexError:
            pass
        return game_ids

    def get_meta(self, game_id):
        url = f"http://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"
        response = requests.get(url)
        game_info = ()
        
        if response.status_code == 200:
            game_data = response.json()
            teams = game_data.get('gameData', {}).get('teams', {})
            away_team_name = teams.get('away', {}).get('name')
            home_team_name = teams.get('home', {}).get('name')
            away_pitcher_name = game_data.get('gameData', {}).get('probablePitchers', {}).get('away', {}).get('fullName')
            home_pitcher_name = game_data.get('gameData', {}).get('probablePitchers', {}).get('home', {}).get('fullName')
            away_pitcher_id = game_data.get('gameData', {}).get('probablePitchers', {}).get('away', {}).get('id')
            home_pitcher_id = game_data.get('gameData', {}).get('probablePitchers', {}).get('home', {}).get('id')
            
        print("This is the 'get_meta' method")

    def createManager(self, gameids):
        NodeList = [] 	#Holds the nodes
        for gameid in gameids:
            Game = Node(gameid)
            NodeList.append(Game)
        
        
        return NodeList
        #Represent each node to the user
        #return the nodes in a list that is accessible by the user entering a key
    
    def access_pitcher_pitching(self,pitcher_id):
        pitcher_id = str(pitcher_id)
        try:
            year = 2024
            pitcher_name = self.pitchers[pitcher_id]['PlayerName']
            player_log = pd.read_csv(f"players/{year}/pitcher_gamelogs/{pitcher_name.replace(' ','_')}_{str(pitcher_id)}.csv")
            

            #Access last 3 games
            #Date, Opp, Pitches Thrown, IP, ER
            df = player_log[['p']]
            print(df)
            try:
                #keep track how many days ago
                games = [pitcher_name, df.iloc[0][0], df.iloc[1][0], df.iloc[2][0]]
            except IndexError:
                try:
                    games = [pitcher_name, df.iloc[0][0]]
                except IndexError:
                    games = [pitcher_name, 0]
                    
            return games
        except KeyError:
            return 'No Games Played..'
  
            
      
        
    def get_starting_pitchers(self, game_ids):
        """ Fetch starting pitchers using game IDs """
        '''Returns	'''
        starting_pitchers = []
        for game_id in game_ids:
            url = f"http://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"
            response = requests.get(url)
            if response.status_code == 200:
                game_data = response.json()
                teams = game_data.get('gameData', {}).get('teams', {})
                
                # Assuming we get the team name from teams, not from the probablePitchers
                away_team = teams.get('away', {}).get('name')
                home_team = teams.get('home', {}).get('name')
                away_pitcher_name = game_data.get('gameData', {}).get('probablePitchers', {}).get('away', {}).get('fullName')
                home_pitcher_name = game_data.get('gameData', {}).get('probablePitchers', {}).get('home', {}).get('fullName')
    
                if away_pitcher_name:
                    starting_pitchers.append({
                        'name': away_pitcher_name,
                        'team': away_team,
                        'opponent': home_team,
                        'location': 'away'
                    })
                if home_pitcher_name:
                    starting_pitchers.append({
                        'name': home_pitcher_name,
                        'team': home_team,
                        'opponent': away_team,
                        'location': 'home'
                    })
        return starting_pitchers

def main():
    def load_strategies(filepath):
        strategies = {}
        with open(filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                player_id = row['Player ID']
                strategies[player_id] = {
                    'Player Name': row['Player Name'],
                    'Strategy': row['Strategy'],
                    'Team': row['Team'],
                    'Hits 2023': row.get('Hits 2023', 'N/A'),
                    'No Hits 2023': row.get('No Hits 2023', 'N/A'),
                    'Hit Percentage 2023': row.get('Hit Percentage 2023', 'N/A'),
                    'Hits 2024': row.get('Hits 2024', 'N/A'),
                    'No Hits 2024': row.get('No Hits 2024', 'N/A'),
                    'Hit Percentage 2024': row.get('Hit Percentage 2024', 'N/A')
                }
        return strategies



    def load_pitcher_stats(filepath):
        with open(filepath) as jsonfile:
            pitcher_stats = json.load(jsonfile)
        return pitcher_stats

    def parse_strategy(strategy):
        conditions = strategy.split('|')
        parsed_conditions = []
        for cond in conditions:
            if '>' in cond:
                key, value = cond.split('>')
                parsed_conditions.append((key, '>', value))
            elif '<' in cond:
                key, value = cond.split('<')
                parsed_conditions.append((key, '<', value))
            elif '=' in cond:
                key, value = cond.split('=')
                parsed_conditions.append((key, '=', value))
        return parsed_conditions


    def evaluate_condition(stat, condition, game_context):
        key, operator, value = condition
        if key.lower() == "location":
            return game_context == value
        if operator == '>':
            return float(stat.get(key, 0)) > float(value)
        elif operator == '<':
            return float(stat.get(key, 0)) < float(value)
        elif operator == '=':
            if key.lower() == 'pitchinghand':  # Case-insensitive comparison for text-based stats
                return stat.get(key, '').lower() == value.lower()
            else:
                return stat.get(key) == value
        return False



    team_codes = {
        "Chicago Cubs": "CHC",
        "Miami Marlins": "MIA",
        "Los Angeles Angels": "LAA",
        "Cincinnati Reds": "CIN",
        "Boston Red Sox": "BOS",
        "Pittsburgh Pirates": "PIT",
        "Chicago White Sox": "CHW",
        "Philadelphia Phillies": "PHI",
        "Washington Nationals": "WSH",
        "Houston Astros": "HOU",
        "Tampa Bay Rays": "TB",
        "New York Yankees": "NYY",
        "Oakland Athletics": "OAK",
        "Cleveland Guardians": "CLE",
        "Texas Rangers": "TEX",
        "Atlanta Braves": "ATL",
        "Baltimore Orioles": "BAL",
        "Kansas City Royals": "KC",
        "Detroit Tigers": "DET",
        "Minnesota Twins": "MIN",
        "Milwaukee Brewers": "MIL",
        "St. Louis Cardinals": "STL",
        "San Diego Padres": "SD",
        "Toronto Blue Jays": "TOR",
        "New York Mets": "NYM",
        "Los Angeles Dodgers": "LAD",
        "San Francisco Giants": "SF",
        "Arizona Diamondbacks": "ARI",
        "Colorado Rockies": "COL",
        "Seattle Mariners": "SEA"
    }
    def normalize_name(name):
        """Normalize names by stripping accents and converting to lowercase."""
        normalized_name = unicodedata.normalize('NFD', name)  # Decompose into base character and diacritics
        stripped_name = ''.join(c for c in normalized_name if unicodedata.category(c) != 'Mn')  # Remove diacritics
        return stripped_name.lower().replace(' ', '')

    def find_pitcher_stat(pitcher_name, pitcher_stats):
        """Find and return the stats for a pitcher given their name."""
        normalized_name = normalize_name(pitcher_name)
        normalized_name = normalized_name.replace('.','')
        #print(normalized_name)  # Debugging to see the normalized name
        for stats in pitcher_stats.values():
            if normalize_name(stats.get('fullName', '')) == normalized_name:
                return stats
        return None

    def evaluate_strategies(strategies, pitcher_stats, starting_pitchers, thresh):
        valid_strategies = []
        print("\n\nEvaluating strategies...")
        for pitcher_info in starting_pitchers:
            opponent_team_code = team_codes.get(pitcher_info['opponent'], "")
            pitcher_stat = find_pitcher_stat(pitcher_info['name'], pitcher_stats)
            if pitcher_stat:
                if float(pitcher_stat.get('IP', 0)) >= thresh:
                    for strategy_info in strategies.values():
                        if strategy_info['Team'] == opponent_team_code:
                            strategy_conditions = parse_strategy(strategy_info['Strategy'])
                            game_context = 'home' if pitcher_info['location'] == 'away' else 'away'
                            condition_results = [evaluate_condition(pitcher_stat, cond, game_context) for cond in strategy_conditions]
                            if all(condition_results):
                                # Sum the Hits and No Hits from both years
                                total_hits = int(strategy_info.get('Hits 2023', 0)) + int(strategy_info.get('Hits 2024', 0))
                                total_no_hits = int(strategy_info.get('No Hits 2023', 0)) + int(strategy_info.get('No Hits 2024', 0))
                                
                                # Calculate the combined Hit Percentage
                                combined_hit_percentage = (total_hits / (total_hits + total_no_hits)) * 100 if (total_hits + total_no_hits) > 0 else 0
                                
                                valid_strategies.append(
                                    f"\n{strategy_info['Player Name']} strategy is valid against {pitcher_info['name']} at {game_context}. "
                                    f"Total Hits: {total_hits}, Total No-Hits: {total_no_hits}, "
                                    f"Combined Record Percentage: {combined_hit_percentage:.2f}%, Conditions: {strategy_conditions}")
                else:
                    print(f"{pitcher_info['name']} has pitched less than 10 innings this season.")
            else:
                print(f"No stats found for {pitcher_info['name']}")
        return valid_strategies





    strategies = load_strategies('strategies/player_strategies.csv')
    pitcher_stats = load_pitcher_stats('players/2024/pitcher_metadata.json')

    today = Today()
    starting_pitchers = today.get_starting_pitchers(today.get_game_ids())
    print('\nTodays Starting Pitchers\n')
    for pitcher in starting_pitchers:
        print(pitcher['name'])
    valid_strategies_today = evaluate_strategies(strategies, pitcher_stats, starting_pitchers,thresh=10.0)
    for strategy in valid_strategies_today:
        print(strategy)
