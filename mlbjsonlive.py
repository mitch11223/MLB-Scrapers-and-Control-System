import pandas as pd
import requests
import json
import os
#THIS SCRIPT APPENDS TEH FANGRAPS DATA TO THE METDATA
import json
import pandas as pd
import numpy as np
from pybaseball import pitching_stats
import unicodedata
import re

#HELPER
def get_game_ids(directory): 
    game_ids = []
    for filename in os.listdir(directory):
        if filename.startswith('.') or not filename.endswith('.json'):
          continue

        game_id = filename[:6]
        if game_id.isdigit():
          game_ids.append(game_id)

    return game_ids


def process_description(description, plate_appearance):
    if description in ['In play, out(s)', 'In play, no out','In play, run(s)']:
        description = plate_appearance.get('event')
        return description
    
    if description == 'Swinging Strike (Blocked)':
        description = 'Swinging Strike'
        return description
    
    if description == 'Ball In Dirt':
        description = 'Ball'
        return description
    
    if description == 'Foul Tip':
        description = 'Swinging Strike'
        return description
    
    if description == 'Foul Bunt':
        description = 'Foul'
        return description
    
    return description


def normalize_name(name):
    name = unicodedata.normalize('NFD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r"\W+", '', name.lower())
    if name in ['Mike Soroka','mikesoroka']:
        name = 'michaelsoroka'
    if name in ['Luis L. Ortiz']:
        name = 'luislortiz'
    if name in ['j.p.france']:
        name = 'jpfrance'
        
    return name

   
   
#MAIN
def update_batter_logs(plate_appearance_log, season, pitchers_data):
    """
    Updates plate appearance logs to include opponent pitcher attributes.

    Args:
      plate_appearance_log (pd.DataFrame): DataFrame containing plate appearance information.
      season (str): The season for which the data belongs to.
      pitchers_data (dict): Dictionary containing pitcher data with pitcher ID as keys. pitcher_metadata.json
    """
    

    for index, row in plate_appearance_log.iterrows():
        pitcher_id = row['pitcher_id']
        pitcher_info = pitchers_data.get(str(pitcher_id), {})
        for key, value in pitcher_info.items():
            # Add pitcher data as columns with corresponding values
            plate_appearance_log.loc[index, f'{key}'] = value
    
    #print(plate_appearance_log)
    return plate_appearance_log


def save_batter_logs(plate_appearance_log, season):
    """
    Saves plate appearance data for each unique batter in a DataFrame to CSV files.

    Args:
      plate_appearance_log (pd.DataFrame): DataFrame containing plate appearance information.
      season (str): The season for which the data belongs to.
    """

    unique_batter_ids = plate_appearance_log['batter_id'].unique()

    with open(f"players/{season}/batter_metadata.json",'r') as f:
        batters = json.load(f)
        
    players_dir = f'players/{season}/PlateAppearanceLogs/batter'
    os.makedirs(players_dir, exist_ok=True)

    for batter_id in unique_batter_ids:
        try:
            batter_name = batters[str(batter_id)]['fullNameAlt']
            batter_name = batter_name.replace(' ','_')
            batter_log = plate_appearance_log[plate_appearance_log['batter_id'] == batter_id]
            output_file = f'{players_dir}/{batter_name}_{batter_id}_log.csv'

            if os.path.isfile(output_file):
              existing_log = pd.read_csv(output_file)
              combined_log = pd.concat([existing_log, batter_log], ignore_index=True)
            else:
                combined_log = batter_log
            combined_log.to_csv(output_file, index=False)
        except KeyError:
            pass




def save_pitches(Type, season, pitches_df, game_id = None):
    
    if game_id:
        pitches_df.to_csv(f'Curve/PitchLogs/{season}/{game_id}.csv', index=False)
    
    else:
        unique_player_ids = pitches_df[f'{Type}_id'].unique()
        with open(f"players/{season}/{Type}_metadata.json",'r') as f:
            players = json.load(f)
        players_dir = f'players/{season}/PlateAppearanceLogs/{Type}_pitches'
        os.makedirs(players_dir, exist_ok=True)

        for player_id in unique_player_ids:
            try:
                if Type == 'batter':
                    player_name = players[str(player_id)]['fullNameAlt']
                elif Type == 'pitcher':
                    player_name = players[str(player_id)]['PlayerName']
                
                player_name = player_name.replace(' ','_')
                
                player_log = pitches_df[pitches_df[f'{Type}_id'] == player_id]
                output_file = f'{players_dir}/{player_name}_{player_id}_log.csv'

                if os.path.isfile(output_file):
                  existing_log = pd.read_csv(output_file)
                  combined_log = pd.concat([existing_log, player_log], ignore_index=True)
                else:
                    combined_log = player_log
                combined_log.to_csv(output_file, index=False)
            except KeyError:
                pass




def create_PlateAppearanceLog(season, game_data, pitchers):
    """
    Extracts plate appearance data from a game and creates a DataFrame log.

    Args:
      game_data (dict): Dictionary containing MLB API game data.
      pitchers (dict): Pitchers metadata

    Returns:
      pd.DataFrame: A DataFrame with plate appearance information.
    """
    
    all_plays = game_data.get('liveData', {}).get('plays', {}).get('allPlays', [])
    meta = {'date': game_data.get('gameData', {}).get('datetime', {}).get('officialDate'),
            'gameId': game_data.get('gamePk')}
    
    plate_appearances = []
    all_pitches_df = pd.DataFrame()
    
    
    for play in all_plays:
        result_data = {key: play.get('result', {}).get(key) for key in ['event', 'eventType', 'isOut']}
        matchup_data = {
            'batter_id': play.get('matchup', {}).get('batter', {}).get('id'),
            'pitcher_id': play.get('matchup', {}).get('pitcher', {}).get('id'),
            'batter_name': play.get('matchup', {}).get('batter', {}).get('fullName'),
            'pitcher_name': play.get('matchup', {}).get('pitcher', {}).get('fullName'),
        }

        
        # (Optional) Implement logic to extract runner data if needed
        runners_data = {
            'rob': 1 if len(play['runners']) > 1 else 0
        }
        
        #access play events, last eventid for main... pitches can be built separately below
        play_id = {'playID': play.get('playEvents', [])[-1].get('playId', 'N/A')}
        plate_appearance = {**meta, **result_data, **matchup_data, **runners_data, **play_id}
        plate_appearances.append(plate_appearance)
        
        
        current_play = play
        
        #For each pitcher, try and quanitify command, stuff, consistecy, by going through each pitch and processing
        
        current_play_events = current_play.get('playEvents', [])
        current_play_pitches = [event for event in current_play_events if event.get('isPitch') == True]
        
        
      
        for data in current_play_pitches:
            description = data['details']['call']['description']		#'Called Strike'
            
            description = process_description(description, plate_appearance)
            
            pitch_type = data.get('details', {}).get('type', {}).get('description', 'N/A')			#'Curveball'
            pitch_data = data['pitchData']					#'Micro Pitch Data'
            coordinates_data = pitch_data['coordinates']
            
            
            pitch_data_flat = {'startSpeed': pitch_data.get('startSpeed', 'n/a'), 'endSpeed': pitch_data.get('endSpeed', 'n/a'),
                               'strikeZoneTop': pitch_data.get('strikeZoneTop', 'n/a'), 'strikeZoneBottom': pitch_data.get('strikeZoneBottom', 'n/a'),
                               'zone': pitch_data.get('zone', 'n/a'), 'x':pitch_data.get('coordinates', {}).get('x', 'n/a'), 'y':pitch_data.get('coordinates', {}).get('y', 'n/a'),
                               'pX' : pitch_data.get('coordinates', {}).get('pX', 'n/a'), 'pY' : pitch_data.get('coordinates', {}).get('pZ', 'n/a'), 
                               'verticalMovement': pitch_data.get('breaks', {}).get('breakVertical', 'n/a'),
                               'horizontalMovement': pitch_data.get('breaks', {}).get('breakHorizontal', 'n/a')}
            
            
            row_to_append = {
                'gameId': meta['gameId'],
                'pitcher_id': matchup_data['pitcher_id'],
                'pitcher_name': matchup_data['pitcher_name'],
                'batter_id': matchup_data['batter_id'],
                'batter_name': matchup_data['batter_name'],
                'description': description,
                'type': pitch_type,
                **pitch_data_flat,

            }


            all_pitches_df = pd.concat([all_pitches_df, pd.DataFrame([row_to_append])], ignore_index=True)

          
        
   
        
        #Want to be able to go through each pitcher/startingpitchers appearance, and append data from their pitches to the gamelogs
        #Want to be able tp go through each lineup, create auto columns wther the player was in the lineup for each gamelog
        
        
        
        '''
        for play_event in play.get('playEvents', []):			#a list of all events, consits of pitches, meta or other?
            play_id = play_event['playId']
        #track pitchers pitch data? create a db per pitcher, and append pitch data averages, amount of 'hittable' track command?...
        '''  
           
        
    
    
    #Save pitches logs : where?
    save_pitches('pitcher', season, all_pitches_df)
    save_pitches('batter', season, all_pitches_df)
    save_pitches('n/a', season, all_pitches_df, game_id = meta['gameId'])
    
    return pd.DataFrame(plate_appearances)						# Create the DataFrame from the list of plate appearances







seasons = ['2024']
for season in seasons:
    games_directory = f'games/{season}/'
    game_ids = get_game_ids(games_directory)  # Assuming get_game_ids exists
    with open(f'players/{season}/pitcher_metadata.json','r') as f:
        pitchers = json.load(f)
        
    for game_id in game_ids:
        url = f"http://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"
        #if not os.path.exists(f'Curve/PlateAppearanceLogs/{season}/{game_id}_log.csv'):
        print(f"Trying game_id: {game_id}")
        response = requests.get(url)

        if response.status_code == 200:
            game_data = response.json()
            PlateAppearanceLog = create_PlateAppearanceLog(season, game_data, pitchers)
            #Collect the players, save to their own files and update there?
            #for each unique batterid, take all rows it appears in, try to open players own Plate Appearance logs, if n/a then create the DF and append the rows
            
            
            #Save pitcher logs??
            #Sorting batter PlateAppearances by oppPitcherAttributes -- In another script
            #Sorting pitcher PlateAppearances by oppBatterAttributes (not implemented yet)                
            PlateAppearanceLog = update_batter_logs(PlateAppearanceLog, season, pitchers)
            save_batter_logs(PlateAppearanceLog, season)
            
            PlateAppearanceLog.to_csv(f"Curve/PlateAppearanceLogs/{season}/{game_id}_log.csv")
    
    
    
    
 

        
        
        
        #Go through each game in the season PlateAppearances logs, collect, construct and save the players own log
        
#after each game has a dataframe of the players plate appearance data, result and opposing pitcher,pitcherid
#go through each batter in batter_metadata.json



#build a dataframe of just that players plate appeareances in DIR:'players/{year}/{position}_app/plate_appearances.csv'

    
#link = f"https://sporty-clips.mlb.com/{play_id}.mp4"
#link = https://fastball-clips.mlb.com/{game_id}/home/{play_id}.m3u8