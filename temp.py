# X : RUN EVERY DAY



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
                team_runs = game_data[team_key]['teamStats']['batting']['runs']
                opp_runs = game_data[team_key]['teamStats']['pitching']['runs']
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
                    **opposing_pitcher_stats
                }

                if team not in team_game_logs:
                    team_game_logs[team] = []
                team_game_logs[team].append(stats)

    for team, games in team_game_logs.items():
        if games:
            df = pd.DataFrame(games)
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








###combine and place team gamelogs in 'teams/2023+/team_gamelogs/ARI_gamelogs.csv' for example. 
