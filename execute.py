'''
gamePk = int(input('Input a game id in form xxxxx: \n\n'))
print(statsapi.boxscore(gamePk, battingBox=True, battingInfo=True, fieldingInfo=True, pitchingBox=True, gameInfo=True, timecode=None))
'''

   
 

import os
import statsapi
import json


def save_game_data(game_id, data):
    with open(f"games/2024/{game_id}_log.json", "w") as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Data saved as games/2024/{game_id}_log.json")




def collect_game_data(start_date, end_date, team_id=None, opponent_id=None):
    saved_game_ids = set()
    saved_pitcher_ids = set()
    for filename in os.listdir("games/2024"):
        if '._' not in filename:
            if filename.endswith("_log.json"):
                print(filename)  # Print out the filename to understand its structure
                game_id = filename.split("_")[0]  # Adjust the index to match the game ID position in the filename
                saved_game_ids.add(int(game_id))

    games = statsapi.schedule(start_date=start_date, end_date=end_date, team=team_id, opponent=opponent_id)

    for game in games:
        game_id = game['game_id']
        if game_id not in saved_game_ids:
            game_data = statsapi.boxscore_data(game_id)
            save_game_data(game_id, game_data)

            # Extract pitcher data and save it
            for pitching_team in ['home', 'away']:
                for pitcher in game_data['teams'][pitching_team]['pitchers']:
                    pitcher_id = pitcher['person_id']
                    if pitcher_id not in saved_pitcher_ids:
                        pitcher_data = statsapi.player_stat_data(pitcher_id, type='season')



collect_game_data(start_date='2024-03-28', end_date='2024-08-31', team_id="", opponent_id="")




import os
import json
import datetime
import pandas as pd
import requests
import pybaseball
import numpy as np

processed_logs = set()  # Initialize a set to store processed game log filenames

# Define the mapping between Pybaseball column names and desired column names
column_mapping = {
    'ERA': 'ERA',
    'xERA': 'xERA',
    'Contact%': 'CONTACT_PCT',
    'K/9': 'STRIKE_OUTS_PER_9_INNINGS',
    'FBv': 'FBV',
    'wFB/C': 'WFB_C',
    'Location+': 'LOCATION_PLUS',
    'Stuff+': 'STUFF_PLUS',
    # New columns based on your descriptions
    'FB% 2': 'FB_PCT_2',
    'FBv': 'FBV',  # Fastball velocity
    'SL%': 'SL_PCT',
    'SLv': 'SLV',
    'CT%': 'CT_PCT',
    'CTv': 'CTV',
    'CB%': 'CB_PCT',
    'CBv': 'CBV',
    'CH%': 'CH_PCT',
    'CHv': 'CHV',
    'SF%': 'SF_PCT',
    'SFv': 'SFV',
    'KN%': 'KN_PCT',
    'KNv': 'KNV',
    'wFB/C': 'WFB_C',
    'wSL/C': 'WSL_C',
    'wCT/C': 'WCT_C',
    'wCB/C': 'WCB_C',
    'wCH/C': 'WCH_C',
    'wSF/C': 'WSF_C',
    'wKN/C': 'WKN_C',
}

import unicodedata

def normalize_name(name):
    return ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')

def fetch_and_append_handness_to_players(json_file, category):
    if not os.path.exists(json_file):
        print(f"File {json_file} does not exist.")
        return

    if '._' in json_file:
        return
    print('jsonfile', json_file, 'category', category)
    try:
        with open(json_file, 'r') as file:
            try:
                player_data = json.load(file)
            except json.decoder.JSONDecodeError:
                print(f"Error: Unable to load JSON data from {json_file}. The file might be empty or not in proper JSON format.")
                return
            
        pitching_data = pybaseball.pitching_stats(2024, qual=3)
        for player_id, data in player_data.items():
            if 'throwingHand' not in data:  
                print(f"Fetching metadata for {category} ID: {player_id}")
                batting_hand, pitching_hand, player_name = fetch_player_handness(player_id)
                data['BattingHand'] = batting_hand
                data['PitchingHand'] = pitching_hand
                data['PlayerName'] = player_name  # Add player's full name
                
                # Update the code to add pitching stats to player data
                if category == 'pitcher':
                    normalized_player_name = normalize_name(player_name)  # Normalize player name
                    player_pitching_data = pitching_data[pitching_data['Name'].apply(normalize_name) == normalized_player_name]
                    print('here')
                    print(player_pitching_data.columns)
                    if not player_pitching_data.empty:
                        # Add specified columns from cols to the player's data in JSON
                        for pybaseball_col, desired_col in column_mapping.items():
                            if pybaseball_col in player_pitching_data.columns:
                                value = player_pitching_data[pybaseball_col].iloc[0]
                                # Check if the value is NaN before adding it to JSON data
                                if not pd.isna(value):
                                    data[desired_col] = value
                        print(f"Pitching stats added to {category} metadata.")
                    else:
                        print(f"No pitching stats found for {player_name}.")
            
        try:
            with open(json_file, 'w') as file:
                json.dump(player_data, file, indent=4)
                print(f"Handness information and pitching stats appended to {category} metadata JSON.")
        except Exception as e:
            print(f"Error appending handness information and pitching stats to {category} metadata JSON: {e}")
    except KeyError as e:
        print(f'Key error: {e} in {category}')



def fetch_player_handness(person_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{person_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'people' in data and len(data['people']) > 0:
            player_info = data['people'][0]
            batting_hand = player_info.get('batSide', {}).get('description')
            pitching_hand = player_info.get('pitchHand', {}).get('description')
            player_name = player_info.get("nameFirstLast")
            return batting_hand, pitching_hand, player_name
        else:
            print(f"No player information found for ID {person_id}.")
            return None, None, None
    else:
        print(f"Failed to fetch data for player ID {person_id}. Status code: {response.status_code}")
    return None, None, None


def update_player_handness(json_folder):
    for file in os.listdir(json_folder):
        if file.endswith("_metadata.json") and not file.startswith("._"):
            json_file = os.path.join(json_folder, file)
            category = file.split("_")[0]
            fetch_and_append_handness_to_players(json_file, category)


def update_player_json(json_file, data):
    try:
        with open(json_file, 'w') as file:
            json.dump(data, file, indent=4)
            print(f"JSON data saved to {json_file}")
    except Exception as e:
        print(f"Error saving JSON data to file: {e}")

def process_game_log(game_log_path, player_game_logs, pitcher_game_logs):
    global processed_logs  # Access the global set of processed logs
    if game_log_path in processed_logs:
        print(f"Skipping already processed game log: {game_log_path}")
        return
    processed_logs.add(game_log_path)  # Add the game log to the set of processed logs
    
    with open(game_log_path, 'r') as file:
        game_data = json.load(file)
    
    game_id_parts = game_data['gameId'].split('/')
    game_date_str = '/'.join(game_id_parts[:3])  # Extract date part from gameId
    game_date = datetime.datetime.strptime(game_date_str, '%Y/%m/%d').date()
    today = datetime.date.today()
  
    # Skip processing if the game is scheduled for today or has not happened yet
    if game_date >= today:
        return
    
    away_abbreviation = game_data['teamInfo']['away']['abbreviation']
    home_abbreviation = game_data['teamInfo']['home']['abbreviation']
    
    away_pitchers = game_data['awayPitchers']
    home_pitchers = game_data['homePitchers']
    
    update_pitcher_game_logs(away_pitchers, pitcher_game_logs)
    update_pitcher_game_logs(home_pitchers, pitcher_game_logs)
    
    opposing_pitchers = {'home': away_pitchers[1]['personId'] if len(away_pitchers) > 1 else None,
                         'away': home_pitchers[1]['personId'] if len(home_pitchers) > 1 else None}

    away_batters = game_data['awayBatters'][1:]
    home_batters = game_data['homeBatters'][1:]
    
    process_players(away_batters, game_data['playerInfo'], game_data['gameBoxInfo'], player_game_logs, 'away', home_abbreviation, game_date, opposing_pitchers, pitcher_game_logs,away_abbreviation)
    process_players(home_batters, game_data['playerInfo'], game_data['gameBoxInfo'], player_game_logs, 'home', away_abbreviation, game_date, opposing_pitchers, pitcher_game_logs,home_abbreviation)

def update_pitcher_game_logs(pitchers, pitcher_game_logs):
    for pitcher in pitchers:
        person_id = pitcher.get('personId')
        if 'Pitchers' not in pitcher['namefield'] and person_id != 0:
            if person_id not in pitcher_game_logs:
                print(f"Fetching metadata for pitcher ID: {person_id}")
                _, pitching_hand, player_name = fetch_player_handness(person_id)
                print(f"Metadata fetched: Pitching hand: {pitching_hand}")
                pitcher_game_logs[person_id] = {'PitchingHand': pitching_hand, 'PlayerName': player_name}


def process_players(players, player_info, game_info, player_game_logs, team_location, opponent_abbreviation, game_date, opposing_pitchers, pitcher_game_logs, team_name):
    for player in players:
        person_id = player.get('personId')
        if person_id is not None and not str(person_id).endswith(')'):
            player_data = player_info.get(('ID' + str(person_id)))
            if player_data is not None:
                player_name = player_data.get('fullName')
                print(f"Fetching metadata for player ID: {person_id}")
                batting_hand, _, _ = fetch_player_handness(person_id)
                print(f"Metadata fetched: Batting hand: {batting_hand}")
                game_log = {key: value for key, value in player.items() if key != 'namefield'}
                game_log['TeamName'] = team_name
                game_log['BattingHand'] = batting_hand
                for info in game_info:
                    label = info.get('label', '')
                    value = info.get('value', '')
                    if label in ['Weather', 'Wind', 'First pitch', 'Att']:
                        if label == 'Weather':
                            temp, cond = value.split(', ')
                            game_log['Temp'] = temp.split()[0]
                            game_log['Condition'] = cond
                        elif label == 'Wind':
                            wind_parts = value.split(', ')
                            wind_speed = wind_parts[0].split()[0]  # Extract wind speed
                            game_log['WindSpeed'] = wind_speed
                            if len(wind_parts) > 1:
                                rest = wind_parts[1]
                                parts = rest.split(' ')
                                if len(parts) >= 4:
                                    wind_direction = parts[1]
                                    wind_destination = ' '.join(parts[3:])
                                    game_log['WindDirection'] = wind_direction if wind_direction != 'R' else 'Right'
                                    game_log['WindDestination'] = wind_destination
                                else:
                                    game_log['WindDirection'] = 'N/A'
                                    game_log['WindDestination'] = 'N/A'
                            else:
                                game_log['WindDirection'] = 'N/A'
                                game_log['WindDestination'] = 'N/A'

                        elif label == 'First pitch':
                            game_log['GameStartTime'] = value.rstrip('.')
                
                try:
                    game_log['Opponent'] = opponent_abbreviation
                    game_log['GameDate'] = game_date.isoformat()  # Convert date to string
                    game_log['TeamLocation'] = team_location
                    
                    # Assign opposing pitcher's ID to the game log data
                    opponent_pitcher_id = opposing_pitchers[team_location]
                    game_log['OpposingPitcherId'] = opponent_pitcher_id
                    
                    if opponent_pitcher_id in pitcher_game_logs:
                        print('opponent pitching ID in gamelogs')
                        opponent_pitcher_data = pitcher_game_logs[opponent_pitcher_id]
                        game_log['OpposingPitcherName'] = opponent_pitcher_data.get('PlayerName', 'N/A')
                        game_log['OpposingPitcherPitchingHand'] = opponent_pitcher_data.get('PitchingHand', 'N/A')

                    if person_id not in player_game_logs:
                        player_game_logs[person_id] = {'PlayerName': player_name, 'GameLogs': []}
                        
                    player_game_logs[person_id]['GameLogs'].append(game_log)
                    
                except KeyError as e:
                    print(f'KeyError: {e}')
                except TypeError as te:
                    print(f'TypeError: {te} occurred while processing player ID: {person_id}')
                    # Handle the TypeError here, such as logging the error or assigning a default value
                    



def process_game_logs(year):
    player_game_logs = {}
    pitcher_game_logs = {}
    
    def process_game_logs_directory(directory_path):
        for filename in os.listdir(directory_path):
            if not filename.startswith("._") and filename.endswith("_log.json"):
                game_log_path = os.path.join(directory_path, filename)
                print(f"Processing game log: {game_log_path}")
                process_game_log(game_log_path, player_game_logs, pitcher_game_logs)

                if os.path.isdir(game_log_path):
                    process_game_logs_directory(game_log_path)
    
    process_game_logs_directory(f"games/{year}")

    # Save batter data to a JSON file
    with open(os.path.join('players', '2024', 'batter_metadata.json'), 'w') as file:
        json.dump(player_game_logs, file, indent=4)
  

    # Save pitcher data to a JSON file
    with open(os.path.join('players', '2024', 'pitcher_metadata.json'), 'w') as file:
        json.dump(pitcher_game_logs, file, indent=4)
 
    # Create CSV logs for each player
    create_player_csv_logs(os.path.join('players', '2024', 'batter_metadata.json'), 'players/2024/batter_gamelogs')
    create_player_csv_logs(os.path.join('players', '2024', 'pitcher_metadata.json'), 'players/2024/pitcher_gamelogs')

def create_player_csv_logs(player_metadata_file, output_folder):
    with open(player_metadata_file, 'r') as file:
        player_data = json.load(file)
    
    for player_id, data in player_data.items():
        player_name = data['PlayerName']
        game_logs = data.get('GameLogs', [])
        if game_logs:
            game_logs_df = pd.DataFrame(game_logs)
            game_logs_df.to_csv(os.path.join(output_folder, f"{player_name}_log.csv"), index=False)


#insert here
cols = ['ERA','xERA','CONTACT_PCT',
        'STRIKE_OUTS_PER_9_INNINGS','FBV','WFB_C','LOCATION_PLUS','STUFF_PLUS','FB_PCT_2']

update_player_handness("players/2024")
process_game_logs(2024)


file_path = 'players/2024/batter_gamelogs'
player_data_path = 'players/2024/pitcher_metadata.json'

# Load player metadata from JSON file
with open(player_data_path, 'r') as f:
    player_data = json.load(f)
                
for file in os.listdir(file_path):
    if file.endswith("_log.csv") and (not file.startswith("._") or not file.startswith("_.")):
        try:
            player_logs = pd.read_csv(os.path.join(file_path, file))
            
            # Loop through each row in player_logs DataFrame
            for index, row in player_logs.iterrows():
                # Match OpposingPitcherId to a key in player_data
                opposing_pitcher_id = row['OpposingPitcherId']
                
                # Retrieve pitcher metadata from player_data using OpposingPitcherId as key
                pitcher_metadata = player_data.get(str(opposing_pitcher_id), {})
                
                # Extract required pitcher stats from pitcher_metadata
                era = pitcher_metadata.get('ERA', None)
                xera = pitcher_metadata.get('xERA', None)
                fbv = pitcher_metadata.get('FBV', None)
                wfb_c = pitcher_metadata.get('WFB_C', None)
                location_plus = pitcher_metadata.get('LOCATION_PLUS', None)
                stuff_plus = pitcher_metadata.get('STUFF_PLUS', None)
                contact_pct = pitcher_metadata.get('CONTACT_PCT', None)
                k_nine = pitcher_metadata.get('STRIKE_OUTS_PER_9_INNINGS', None)
                
                # Add new columns for the retrieved stats (if not already existing)
                player_logs.loc[index, 'ERA'] = era
                player_logs.loc[index, 'xERA'] = xera
                player_logs.loc[index, 'CONTACT_PCT'] = contact_pct
                player_logs.loc[index, 'FBV'] = fbv
                player_logs.loc[index, 'WFB_C'] = wfb_c
                player_logs.loc[index, 'LOCATION_PLUS'] = location_plus
                player_logs.loc[index, 'STUFF_PLUS'] = stuff_plus
                player_logs.loc[index, 'K/9'] = k_nine
                #insert here
            
            # Save the updated player gamelog back to its file
            player_logs.to_csv(os.path.join(file_path, file), index=False)
            
        except UnicodeDecodeError:
            print(print(os.path.join(file_path, file)), 'passed')
