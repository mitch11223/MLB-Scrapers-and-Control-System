#!/usr/local/bin/python3.11


import unicodedata
import os
import statsapi
import json
import time
import shutil



part_one = True						#Modularized_execute
part_two = True						#mlbjsonlive
part_three = True					#teams



if part_one:
    #THIS SCRIPT COLLECTS AND SAVES THE GAME JSONS

    today = time.strftime('%Y-%m-%d')
    #today = '2024-09-20'

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

        games = statsapi.schedule(start_date=start_date, end_date=today, team=team_id, opponent=opponent_id)
        
        count = 0
        for game in games:
            count += 1
            game_id = game['game_id']
            if game_id not in saved_game_ids:
                game_data = statsapi.boxscore_data(game_id)
                if game_data['homePitchingTotals']['ip'] != "0.0":
                    save_game_data(game_id, game_data)
                else:
                    print(game_id,'passed')
        print(f'Total Games Played: {count}')




    collect_game_data(start_date='2024-03-28', end_date=today, team_id="", opponent_id="")




    #THIS SCRIPT CREATES THE ORIGINAL METADATA
    import os
    import json
    import re

    def normalize_name(name,t):
        name = unicodedata.normalize('NFD', name)
        name = name.encode('ascii', 'ignore').decode('ascii')
        if t == 'pitcher':
            name = re.sub(r"\W+", '', name.lower())
        return name

    def load_game_data(filepath):
        with open(filepath, 'r') as file:
            return json.load(file)

    def save_metadata(data, filename):
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Metadata saved as {filename}")

    def collect_player_metadata(directory):
        pitcher_metadata = {}
        batter_metadata = {}
        
        # Iterate over each game file in the directory
        for filename in os.listdir(directory):
            if filename.endswith(".json") and not (filename.startswith('._') or filename.startswith('._')):
                game_data = load_game_data(os.path.join(directory, filename))
                
                # Process each team (home and away)
                for team_key in ['home', 'away']:
                    team_data = game_data[team_key]
                    
                    # Process pitchers
                    for pitcher_id in team_data['pitchers']:
                        if pitcher_id not in pitcher_metadata:
                            pitcher_metadata[pitcher_id] = game_data['playerInfo']['ID' + str(pitcher_id)]
                            pitcher_name = pitcher_metadata[pitcher_id]['fullName']
                            pitcher_name = normalize_name(pitcher_name,t='pitcher')
                            pitcher_metadata[pitcher_id]['fullName'] = pitcher_name
                    
                    # Process batters
                    for batter_id in team_data['batters']:
                        if batter_id not in pitcher_metadata:
                            if batter_id not in batter_metadata:
                                batter_metadata[batter_id] = game_data['playerInfo']['ID' + str(batter_id)]
                                batter_name = batter_metadata[batter_id]['fullName']
                                batter_name_alt = normalize_name(batter_name,t='batter')
                                batter_name = normalize_name(batter_name,t='pitcher')
                                batter_metadata[batter_id]['fullName'] = batter_name
                                batter_metadata[batter_id]['fullNameAlt'] = batter_name_alt
                        

        # Save the collected metadata to JSON files
        save_metadata(pitcher_metadata, "players/2024/pitcher_metadata.json")
        save_metadata(batter_metadata, "players/2024/batter_metadata.json")

    # Directory where the game data JSON files are stored
    game_data_directory = "games/2024"
    collect_player_metadata(game_data_directory)



    #THIS SCRIPT ADDS THE PITCHINGHAND TO METDATA
    import os
    import json
    import requests
    import pandas as pd
    from pybaseball import pitching_stats

    def load_metadata(filepath):
        with open(filepath, 'r') as file:
            return json.load(file)

    def save_metadata(data, filepath):
        with open(filepath, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"Updated metadata saved to {filepath}")

    def fetch_player_handness(person_id):
        url = f"https://statsapi.mlb.com/api/v1/people/{person_id}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            player_info = data['people'][0]
            pitching_hand = player_info.get('pitchHand', {}).get('description', '')
            player_name = player_info.get("fullName")
            return pitching_hand, player_name
        
        return '', '', ''

    def update_pitcher_metadata(filepath):
        player_data = load_metadata(filepath)
        pitching_stats_2024 = pitching_stats(2024).set_index('Name')

        for player_id, details in player_data.items():
            pitching_hand, player_name = fetch_player_handness(player_id)
            details['PitchingHand'] = pitching_hand
            details['PlayerName'] = player_name



        save_metadata(player_data, filepath)

    # Path to the metadata JSON file
    json_filepath = 'players/2024/pitcher_metadata.json'
    update_pitcher_metadata(json_filepath)


      
    #THIS SCRIPT APPENDS TEH FANGRAPS DATA TO THE METDATA
    import json
    import pandas as pd
    import numpy as np
    from pybaseball import pitching_stats

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
        if name in ['Andrew Thorpe','andrewthorpe']:
            name = 'drewthorpe'
            
        return name


    def load_json(filename):
        with open(filename, 'r') as file:
            return json.load(file)

    def save_json(data, filename):
        with open(filename, 'w') as file:
            # Convert any problematic types here before saving
            def convert(item):
                if isinstance(item, np.generic):
                    return np.asscalar(item)
                raise TypeError
            json.dump(data, file, default=convert, indent=4)

    def fetch_fangraphs_data(year, qual):
        df = pitching_stats(year, qual=qual)
        df = df[~((df['Name'] == 'Logan Allen') & (df['Team'] == 'ARI'))]
        df.to_csv(f'players/2024/dataframes/pitcher_{year}.csv')  # Save data for review
        return df



    def append_stats_to_pitchers(json_file, year, cols, qual,option=False):
        statcast_list = ['FA% (sc)', 'FT% (sc)', 'FC% (sc)', 'FS% (sc)', 'FO% (sc)', 'SI% (sc)', 'SL% (sc)', 'CU% (sc)', 'KC% (sc)', 'EP% (sc)', 'CH% (sc)', 'SC% (sc)', 'KN% (sc)', 'UN% (sc)',
                         'wFA/C (sc)', 'wFT/C (sc)', 'wFC/C (sc)', 'wFS/C (sc)', 'wFO/C (sc)', 
                            'wSI/C (sc)', 'wSL/C (sc)', 'wCU/C (sc)', 'wKC/C (sc)', 'wEP/C (sc)', 
                            'wCH/C (sc)', 'wSC/C (sc)', 'wKN/C (sc)',
                         'vFA (sc)', 'vFT (sc)', 'vFC (sc)', 'vFS (sc)', 'vFO (sc)',
                         'vEP (sc)', 'vCH (sc)',
                            'vSI (sc)', 'vSL (sc)', 'vCU (sc)', 'vKC (sc)', 'vEP (sc)']
        data = load_json(json_file)
        pitching_stats_df = fetch_fangraphs_data(year, qual)
        pitching_stats_df['player_name'] = pitching_stats_df['Name'].apply(normalize_name)
        pitching_stats_df.set_index('player_name', inplace=True)

        for pitcher_id, pitcher_info in data.items():
            normalized_name = normalize_name(pitcher_info['PlayerName'])
            if normalized_name in pitching_stats_df.index:
                player_stats = pitching_stats_df.loc[normalized_name]
                if isinstance(player_stats, pd.DataFrame):
                    player_stats = player_stats.iloc[0]  # Take the first row if there are multiple

                for col in cols:
                    if col in player_stats and not pd.isna(player_stats[col]):
                        if option:
                            pitcher_info['statcast'][col] = round(float(player_stats[col]), 3) if isinstance(player_stats[col], np.number) else player_stats[col]
                        else:
                            pitcher_info[col] = round(float(player_stats[col]), 3) if isinstance(player_stats[col], np.number) else player_stats[col]
                
                if 'SI% (sc)' in pitcher_info:
                    pitcher_info['SI%'] = pitcher_info.pop('SI% (sc)')
                
        for pitcher_id, pitcher_info in data.items():
            for col in statcast_list:
                try:
                    pitcher_info[col.replace(' (sc)','')] = pitcher_info.pop(col)
                except KeyError:
                    pass

        save_json(data, json_file)


    #these are the selected columns from dataframes/pitcher_year.csv to copy to the pitcher metadata
    cols = [
        'Team', 'ERA', 'xERA', 'IP','Location+', 'Stuff+', 'Pitching+', 'Contact%', 'K/9', 'BB/9', 'H/9','HR/9','GB/FB',
        'Oppo%','Pull%','Soft%','Hard%','Zone%',
        'SI% (sc)','FA% (sc)', 'FT% (sc)', 'FC% (sc)', 'FS% (sc)', 'FO% (sc)', 'SI% (sc)', 'SL% (sc)', 'CU% (sc)',
        'KC% (sc)', 'EP% (sc)', 'CH% (sc)', 'SC% (sc)', 'KN% (sc)', 'UN% (sc)',
        'vFA (sc)', 'vFT (sc)', 'vFC (sc)', 'vFS (sc)', 'vFO (sc)', 
        'vSI (sc)', 'vSL (sc)', 'vCU (sc)', 'vKC (sc)', 'vEP (sc)', 
        'vCH (sc)', 'vSC (sc)', 'vKN (sc)',
        'wFA/C (sc)', 'wFT/C (sc)', 'wFC/C (sc)', 'wFS/C (sc)', 'wFO/C (sc)', 
        'wSI/C (sc)', 'wSL/C (sc)', 'wCU/C (sc)', 'wKC/C (sc)', 'wEP/C (sc)', 
        'wCH/C (sc)', 'wSC/C (sc)', 'wKN/C (sc)',
        'Stf+ CH', 'Loc+ CH', 'Pit+ CH', 'Stf+ CU', 'Loc+ CU', 'Pit+ CU', 'Stf+ FA', 
        'Loc+ FA', 'Pit+ FA', 'Stf+ SI', 'Loc+ SI', 'Pit+ SI', 'Stf+ SL', 'Loc+ SL', 'Pit+ SL', 'Stf+ KC', 
        'Loc+ KC', 'Pit+ KC', 'Stf+ FC', 'Loc+ FC', 'Pit+ FC', 'Stf+ FS', 'Loc+ FS', 'Pit+ FS'
    ]

    json_filepath = 'players/2024/pitcher_metadata.json'

    append_stats_to_pitchers(json_filepath, 2024, cols, 3)




    #This appends pitch level data to pitcher meta
    from pybaseball import statcast_pitcher_arsenal_stats
    import json
    import pandas as pd


    data = statcast_pitcher_arsenal_stats(2024, minPA=3)

    with open('players/2024/pitcher_metadata.json', 'r') as f:
        pitchers = json.load(f)

    unique_player_ids = data['player_id'].unique()
    
    sl = False
    for player_id in unique_player_ids:
        player_data = data[data['player_id'] == player_id]
        
        if 'SL' in player_data['pitch_type'].values:
            sl = True
        for _, row in player_data.iterrows():
            pitch_type = row['pitch_type']
            
            if not sl:
                if pitch_type == 'ST':
                    pitch_type = 'SL'
            if pitch_type == 'KN':
                pitch_type = 'KC'
            #batting average, slg, whiff for each pitch type
            
            ba = row['ba']
            slg = row['slg']
            whiff = round(row['whiff_percent'] / 100, 3)
            
            pitch_type_key_ba = f"{pitch_type}_ba"
            pitch_type_key_slg = f"{pitch_type}_slg"
            pitch_type_key_whiff = f"{pitch_type}_whiff"
                        
            if str(player_id) in pitchers:
                pitchers[str(player_id)][pitch_type_key_ba] = ba
                pitchers[str(player_id)][pitch_type_key_slg] = slg
                pitchers[str(player_id)][pitch_type_key_whiff] = whiff


    with open('players/2024/pitcher_metadata.json', 'w') as f:
        json.dump(pitchers, f)




    #THIS PART CREATES THE year GAMELOGS

    import json
    import pandas as pd
    import os

    def load_json(filename):
        with open(filename, 'r') as file:
            return json.load(file)

    def save_csv(df, filename):
        df.to_csv(filename, index=False)

    def parse_weather_info(game_data):
        for info in game_data['gameBoxInfo']:
            if info['label'] == "Weather":
                weather_data = info['value']
                temperature = None
                weather = None
                try:
                    temperature_info, weather = weather_data.split(', ')
                    temperature = int(temperature_info.split(' ')[0])
                    if ',' in weather:
                        weather = weather.split(', ')[0]
                except ValueError:
                    # Handle cases where the weather data might be in a different format
                    print(f"Weather data not in expected format: {weather_data}")
                return temperature, weather
        return None, None

    def collect_game_logs(game_data_dir, batters_metadata, pitcher_metadata_path, output_dir):
        batters = load_json(batters_metadata)
        pitchers = load_json(pitcher_metadata_path)
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        player_game_logs = {str(batter_id): [] for batter_id in batters}
        pitcher_game_logs = {str(pitcher_id): [] for pitcher_id in pitchers}

        for game_file in os.listdir(game_data_dir):
            if game_file.endswith(".json") and not game_file.startswith('._'):
                file_path = os.path.join(game_data_dir, game_file)
                with open(file_path, 'r') as file:
                    game_data = json.load(file)
                    game_date = game_data["gameId"][0:10]
                    home_team = game_data["teamInfo"]["home"]["abbreviation"]
                    away_team = game_data["teamInfo"]["away"]["abbreviation"]
                    for value in game_data['gameBoxInfo']:
                        if value['label'] == 'First pitch':
                            game_time = value['value']

                    for team_key in ['home', 'away']:
                        team = game_data["teamInfo"][team_key]["abbreviation"]
                        opponent_team_key = 'away' if team_key == 'home' else 'home'
                        opponent = game_data["teamInfo"][opponent_team_key]["abbreviation"]
                        opponent_pitchers = game_data[opponent_team_key + 'Pitchers'][1:]
                        temperature, weather = parse_weather_info(game_data)

                        
                        for player_info in game_data[f'{team_key}Pitchers'][1:]:
                            player_id = str(player_info['personId'])
                            if player_id in pitcher_game_logs:
                                stats = {
                                    "date": game_date,
                                    'time': game_time,
                                    "opponent": opponent,
                                    "team": team,
                                    "location": team_key,  # Indicates whether the player was at home or away
                                    "weather": weather,
                                    "temp": temperature,
                                    **{key: player_info.get(key, '') for key in [
                                        'ip', 'h', 'r', 'er', 'bb', 'k', 'hr', 'p', 'era'
                                    ]}
                                }
                                pitcher_game_logs[player_id].append(stats)
                                
                        for player_info in game_data[f'{team_key}Batters'][1:]:
                            player_id = str(player_info['personId'])
                            position = player_info['position']
                            
                            if player_id in player_game_logs:
                                opposing_pitcher = opponent_pitchers[0]
                                opposing_pitcher_id = str(opposing_pitcher['personId'])
                                pitcher_data = pitchers.get(opposing_pitcher_id, {})

                                stats = {
                                    "date": game_date,
                                    'time': game_time,
                                    "opponent": opponent,
                                    "team": team,
                                    "location": team_key,  # Indicates whether the player was at home or away
                                    "weather": weather,
                                    "temp": temperature,
                                    "opposingPitcherId": opposing_pitcher_id,
                                    "position": position,
                                    **{key: player_info.get(key, '') for key in [
                                        'ab', 'r', 'h', 'doubles', 'triples', 'hr', 'rbi',
                                        'sb', 'bb', 'k', 'lob', 'avg', 'obp', 'slg', 'ops'
                                    ]},
                                    **pitcher_data
                                }
                                player_game_logs[player_id].append(stats)

        for player_id, games in player_game_logs.items():
            if games:
                df = pd.DataFrame(games).sort_values('date',ascending=False)
                if df['ab'].astype(int).sum() > 1:
                    player_name = batters[player_id]['fullNameAlt'].replace(' ', '_')
                    batters[player_id]['Team'] = df['team'].iloc[0]
                    save_csv(df, os.path.join(output_dir, f"{player_name}_{player_id}.csv"))
                    
        for player_id, games in pitcher_game_logs.items():
            if games:
                #sort df so most recent games at top
                df = pd.DataFrame(games).sort_values('date',ascending=False)
                player_name = pitchers[player_id]['PlayerName'].replace(' ', '_')
                pitchers[player_id]['Team'] = df['team'].iloc[0]
                save_csv(df, os.path.join('players/2024/pitcher_gamelogs', f"{player_name}_{player_id}.csv"))



    #to include meta
    # Paths
    game_data_directory = 'games/2024'
    batters_metadata = 'players/2024/batter_metadata.json'
    pitchers_metadata = 'players/2024/pitcher_metadata.json'
    output_directory = 'players/2024/batter_gamelogs'


    collect_game_logs(game_data_directory, batters_metadata, pitchers_metadata, output_directory)






    #THIS PART CREATES THE 2023+ GAMELOGS

    #this method simply removes (pi) from the json
    def process_json_remove_pi_suffix(file_path='players/2024/pitcher_metadata.json'):
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        updated_data = {}
        for player_id, stats in data.items():
            new_stats = {key.replace(' (pi)', ''): value for key, value in stats.items()}
            updated_data[player_id] = new_stats
        
        save_json(updated_data,file_path)
    process_json_remove_pi_suffix()





    import pandas as pd
    import os

    def load_gamelogs(year, directory_path):
        year_path = os.path.join(directory_path, str(year), 'batter_gamelogs')
        all_data = {}
        if os.path.exists(year_path):
            for file in os.listdir(year_path):
                if file.endswith(".csv") and not file.startswith('._'):
                    file_path = os.path.join(year_path, file)
                    df = pd.read_csv(file_path)
                    player_id = file.split('_')[-1].split('.')[0]  # Extract the player ID from the filename
                    player_name = '_'.join(file.split('_')[:-1])  # Extract the player name from the filename
                    player_key = f"{player_name}_{player_id}"
                    if player_key in all_data:
                        all_data[player_key] = pd.concat([all_data[player_key], df])
                    else:
                        all_data[player_key] = df
                    print(f"Loaded {file} for year {year}")
        else:
            print(f"Directory {year_path} not found.")
        return all_data

    def combine_and_save_gamelogs(directory_path, output_path):
        combined_data = {}
        years = [2023, 2024]
        for year in years:
            yearly_data = load_gamelogs(year, directory_path)
            for key, df in yearly_data.items():
                if key in combined_data:
                    combined_data[key] = pd.concat([combined_data[key], df])
                else:
                    combined_data[key] = df
                print(f"Combining data for {key}")

        if not os.path.exists(output_path):
            os.makedirs(output_path)	
            print(f"Created directory {output_path}")

        for key, df in combined_data.items():
            df['date'] = pd.to_datetime(df['date'])  # Ensure 'date' is datetime type
            df.set_index('date', inplace=True)  # Set 'date' as index
            

            output_file_path = os.path.join(output_path, f"{key}.csv")
            df.to_csv(output_file_path)
            print(f"Saved {output_file_path}")

    # Paths and parameters
    directory_path = 'players'
    output_path = 'players/2023+/batter_gamelogs'

    # Combine and save the gamelogs
    combine_and_save_gamelogs(directory_path, output_path)

    print("Gamelogs combined and saved in the 'players/2023+/batter_gamelogs' directory.")










if part_two:
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
            if not os.path.exists(f'Curve/PlateAppearanceLogs/{season}/{game_id}_log.csv'):
                print(f"Trying game_id: {game_id}")
                response = requests.get(url)

                if response.status_code == 200:
                    try:
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
                    except IndexError:
                        print(f'{game_id} failed IndexError')
            
        
        
       
            
        #link = f"https://sporty-clips.mlb.com/{play_id}.mp4"
        #link = https://fastball-clips.mlb.com/{game_id}/home/{play_id}.m3u8


#PART 3

if part_three:
    #teams

    import json
    import pandas as pd
    import os


    def load_json(filename):
        print(f"Loading JSON file: {filename}")
        try:
            with open(filename, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Failed to load JSON file: {e}")
            return None

    def save_csv(df, filename):
        print(f"Saving CSV file: {filename}")
        try:
            df.to_csv(filename, index=False)
        except Exception as e:
            print(f"Failed to save CSV file: {e}")

    def parse_weather_info(game_data):
        for info in game_data.get('gameBoxInfo', []):
            if info['label'] == "Weather":
                weather_data = info['value']
                temperature = None
                weather = None
                try:
                    temperature_info, weather = weather_data.split(', ')
                    temperature = int(temperature_info.split(' ')[0])
                    if ',' in weather:
                        weather = weather.split(', ')[0]
                except ValueError:
                    print(f"Weather data not in expected format: {weather_data}")
                return temperature, weather
        return None, None

    def parse_time(game_data):
        for info in game_data.get('gameBoxInfo', []):
            if info['label'] == "First pitch":
                first_pitch = info['value']
                return first_pitch

    def collect_team_game_logs(game_data_dir, pitcher_metadata_path, output_dir):
        print("Starting to collect team game logs")
        pitchers = load_json(pitcher_metadata_path)
        if pitchers is None:
            print("No pitchers data available")
            return
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"Game data directory contents: {os.listdir(game_data_dir)}")
        
        team_game_logs = {}
        
        for game_file in os.listdir(game_data_dir):
            if game_file.endswith(".json") and not game_file.startswith('._'):
                file_path = os.path.join(game_data_dir, game_file)
                print(f"Processing file: {file_path}")
                try:
                    with open(file_path, 'r') as file:
                        game_data = json.load(file)
                except Exception as e:
                    print(f"Failed to read game file {file_path}: {e}")
                    continue
                
                game_date = game_data.get("gameId", "")[0:10]
                home_team = game_data["teamInfo"]["home"]["abbreviation"]
                away_team = game_data["teamInfo"]["away"]["abbreviation"]
                for value in game_data['gameBoxInfo']:
                    if value['label'] == 'First pitch':
                        game_time = value['value']
                
                
                for team_key in ['home', 'away']:
                    team = game_data["teamInfo"][team_key]["abbreviation"]
                    if team == 'AZ':
                        team = 'ARI'
                    opponent_team_key = 'away' if team_key == 'home' else 'home'
                    opponent = game_data["teamInfo"][opponent_team_key]["abbreviation"]
                    opponent_pitchers = game_data.get(opponent_team_key + 'Pitchers', [])[1:]
                    opp_runs = game_data[team_key]['teamStats']['pitching']['runs']
                    
                    team_pitchers = game_data.get(team_key + 'Pitchers', [])[1:]
                    team_runs = game_data[team_key]['teamStats']['batting']['runs']
                    
                    if team_runs > opp_runs:
                        result = 'W'
                    if team_runs < opp_runs:
                        result = 'L'
                    if not opponent_pitchers:
                        print(f"No opponent pitchers data for {file_path}")
                        continue
                    temperature, weather = parse_weather_info(game_data)
                    
                    opposing_pitcher = opponent_pitchers[0]
                    opposing_pitcher_id = str(opposing_pitcher['personId'])
                    pitcher_data = pitchers.get(opposing_pitcher_id, {})
                    
                    team_pitcher = team_pitchers[0]
                    team_pitcher_id = str(team_pitcher['personId'])
                    team_pitcher_stats = {
                        "teamPitcherId": team_pitcher_id,
                        "teamPitcherName": pitchers.get(team_pitcher_id, {}).get('PlayerName',''),
                        "teamStarterIP": team_pitcher.get("ip", ""),
                        "teamStarterER": team_pitcher.get("er", ""),
                        "teamStarterK": team_pitcher.get("k", "")
                    }
                        
                    
                    opposing_pitcher_stats = {
                        "oppStarterIP": opposing_pitcher.get("ip", ""),
                        "oppStarterH": opposing_pitcher.get("h", ""),
                        "oppStarterR": opposing_pitcher.get("r", ""),
                        "oppStarterER": opposing_pitcher.get("er", ""),
                        "oppStarterBB": opposing_pitcher.get("bb", ""),
                        "oppStarterK": opposing_pitcher.get("k", ""),
                        "oppStarterHR": opposing_pitcher.get("hr", ""),
                        "oppStarterP": opposing_pitcher.get("p", ""),
                        "oppStarterS": opposing_pitcher.get("s", ""),
                        "oppStarterERA": opposing_pitcher.get("era", "")
                    }

                    team_stats = game_data[team_key].get("teamStats", {})
                    opponent_stats = game_data[opponent_team_key].get("teamStats", {})
                    batting_stats = team_stats.get("batting", {})
                    pitching_stats = team_stats.get("pitching", {})
                    opposing_batting_stats = opponent_stats.get("batting", {})
                    opposing_pitching_stats = opponent_stats.get("pitching", {})
                    
                    opposing_runs = opposing_batting_stats.get('runs', {})

                    stats = {
                        "date": game_date,
                        'time': game_time,
                        'result': result,
                        "time": parse_time(game_data),
                        "opponent": opponent,
                        "team": team,
                        "location": team_key,  # Indicates whether the team was at home or away
                        "weather": weather,
                        "temp": temperature,
                        "opposingPitcherId": opposing_pitcher_id,
                        'oppRuns': opposing_runs,
                        **{key: batting_stats.get(key, '') for key in [
                            'runs', 'doubles', 'triples', 'homeRuns', 'strikeOuts', 'baseOnBalls', 'hits',
                            'atBats', 'stolenBases', 'rbi', 'leftOnBase'
                        ]},
                        **pitcher_data,
                        **opposing_pitcher_stats,
                        **team_pitcher_stats
                    }

                    if team not in team_game_logs:
                        team_game_logs[team] = []
                    team_game_logs[team].append(stats)

        for team, games in team_game_logs.items():
            if games:
                df = pd.DataFrame(games)

                current_series = 0
                series_list = []
                for index, row in df.iterrows():
                    if index > 0 and row['opponent'] == df.at[index - 1, 'opponent']:
                        series_list.append(current_series)
                    else:
                        current_series += 1
                        series_list.append(current_series)
                df.insert(2, 'series', series_list)
                
                save_csv(df, os.path.join(output_dir, f"{team}_gamelogs.csv"))


    # 2024 Paths
    game_data_directory = 'games/2024'
    pitchers_metadata = 'players/2024/pitcher_metadata.json'
    output_directory = 'teams/2024/team_gamelogs'

    collect_team_game_logs(game_data_directory, pitchers_metadata, output_directory)

    # 2023 Paths
    game_data_directory = 'games/2023'
    pitchers_metadata = 'players/2023/pitcher_metadata.json'
    output_directory = 'teams/2023/team_gamelogs'

    collect_team_game_logs(game_data_directory, pitchers_metadata, output_directory)








#for player in players/2024/pitcher_metadata.json
#we need to look at their pitch specific info
#for each pitch, the velocity, efficiceny and frequency are all tracked
#we need to categorize each pitch, and then calculate the weigthed averages for each category
#we will have hard, breaking and offspeed
#for each of these we calculate teh weighted average velocity, efficiency and frequency based off the pitches under each umbrella
#hard will be the weighted avereages of FA,FC,FS, SI
#breaking is CL, CUR, KN
#offspeed is CH,SP
#you must look at the json, and identify how each attributed is constrcuted specifically
