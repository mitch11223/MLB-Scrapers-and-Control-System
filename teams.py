import datetime
import os
import pandas as pd
import time
import strategies
from pybaseball import playerid_reverse_lookup
from pybaseball import get_splits
import json
import warnings
import unicodedata
import re
from utils import Utils
import requests
from lineupscraper import LineupScraper
import time
from tabulate import tabulate
import socket


def check_internet_connection():
    try:
        # Try to resolve a well-known address, e.g., Google's public DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        pass
    return False

pd.set_option('display.max_rows', None)

def convert_date_to_int(date_str):
    return int(date_str.replace('-', ''))

def normalize_name(name):
    return ''.join(e for e in name.lower() if e.isalnum())

def search_player(directory, identifier):
    identifier = normalize_name(identifier)
    for file in os.listdir(directory):
        if file.endswith('.csv') and not file.startswith('._'):
            player_name = '_'.join(file.split('_')[:-1])
            player_id = file.split('_')[-1].split('.')[0]
            if normalize_name(player_name) == identifier:
                return player_name, player_id, os.path.join(directory, file)
    return None, None, None

#This method creates a baseball reference key, for a player name
def create_player_key(name):
    if isinstance(name,str):
        name = normalize_name_key(name)
    parts = name.split('_')
    parts = [part for part in parts if part.lower() not in ['jr.','jr']]
    first_name = parts[0].capitalize()
    last_name = parts[-1].capitalize()
    player_key = (last_name[:5] + first_name[:2] + '01').lower()

    return player_key

def create_player_key_alt(name):
    parts = name.split(' ')
    parts = [part for part in parts if part.lower() not in ['jr.','jr']]
    first_name = parts[0].capitalize()
    last_name = parts[-1].capitalize()
    player_key = (last_name[:5] + first_name[:2] + '01').lower()
    return player_key

def normalize_name_key(name):
    name = unicodedata.normalize('NFD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r"\W+", '', name.lower())
    return name

def get_team_players(directory, team_name):
    team_players = {}
    team_name_normalized = normalize_name(team_name)
    for file in os.listdir(directory):
        if file.endswith('.csv') and not file.startswith('._'):
            df = pd.read_csv(os.path.join(directory, file))
            # Check if the last entry (most recent game) is for the specified team
            if df.empty or normalize_name(df.iloc[-1]['team']) != team_name_normalized:
                continue
            player_name = '_'.join(file.split('_')[:-1])
            player_id = file.split('_')[-1].split('.')[0]
            team_players[normalize_name(player_name)] = player_id
    return team_players

def apply_and_display_filters(df, filters):
    # Splitting the dataset by year
    years = ['2023', '2024']
    results = {}
    for year in years:
        df_year = df[df['date'].str.contains(year)]
        df_filtered = apply_filters(df_year, filters, year)
        if df_filtered.empty:
            results[year] = "Error applying filters or no data matched the criteria."
        else:
            hits, no_hits, hit_percentage = calculate_hit_record(df_filtered)
            results[year] = f"Hits: {hits}, No Hits: {no_hits}, Hit Record: {hit_percentage:.2%}"

    for year, result in results.items():
        print(f"{year} - {result}")




#--------------------------

class Teams():
    def __init__(self,team=None):
        self.team = team									#Tricode
        if self.team is not None:
            try:
                if check_internet_connection():
                    self.opponent = self.get_opponent(self.team)	#Tricode
            except AttributeError:
                pass
            self.name = self.convertTricode(self.team)		#'Guardians'
            try:
                self.batter_ids = self.getLineupIDs()
            except TypeError:
                pass
            self.team_id = self.getTeamID()
            #self.roster = self.getRoster()		#Creates self.position_players abd self.pitchers as well
            
        self.pitchers = self.load_pitchers()
        self.batters = self.load_batters()
        self.PitcherAttributeDatabase = self.read_pitcher_attrs()
        
        
    def set_team(self,team):
        self.team = team
        if self.team is not None:
            try:
                if check_internet_connection():
                    self.opponent = self.get_opponent(self.team)
            except AttributeError:
                pass
            self.name = self.convertTricode(self.team)
            try:
                self.batter_ids = self.getLineupIDs()
            except TypeError:
                pass
            self.team_id = self.getTeamID()
            #self.roster = self.getRoster()
            
    def load_pitchers(self):
        with open('players/2024/pitcher_metadata.json','r') as f:
            pitchers = json.load(f)
        return pitchers
    
    def load_batters(self):
        with open('players/2024/batter_metadata.json','r') as f:
            batters = json.load(f)
        return batters

    def read_pitcher_attrs(self):
        with open('players/2024/pitcher_attributes.json','r') as f:
            pitchers = json.load(f)
        return pitchers
    
    #Team ID Dict
    def getTeamID(self):
        team_id_dict = {
            'LAA':  108,
            'ARI':  109,
            'ATL':  144,
            'BAL':  110,
            'BOS':  111,
            'CWS':  145,
            'CHC':  112,
            'CIN':  113,
            'CLE':  114,
            'COL':  115,
            'DET':  116,
            'HOU':  117,
            'KC':  118,
            'LAD':  119,
            'MIA':  146,
            'MIL':  150,
            'MIN':  142,
            'NYY':  147,
            'NYM':  121,
            'OAK':  133,
            'PHI':  143,
            'PIT':  134,
            'SD':  135,
            'SEA':  136,
            'SF':  137,
            'STL':  138,
            'TB':  139,
            'TEX':  140,
            'TOR':  141,
            'WSN':  120
        }
        
        return team_id_dict[self.team]
    
    
    def execute_action(self,action):
        if action in ['0']:
            self.team_filters()
        if action in ['1','K','k']:
            self.search_team_k(team=self.team)
        if action in ['2']:
            user_strategy = input('Enter a strategy: ')
            self.search_strategy(user_strategy, team=self.team)
        if action in ['3']:
            self.bullpenUsage()
  
        if action in ["'"]:
            opp_starter_id = str(self.get_opp_starter(team=self.team))	#get opp starter and their attributes
            print('\n\n',self.pitchers[opp_starter_id]['PlayerName'])
            opp_starter_attr = self.get_attr(opp_starter_id)	#formatted like user strategy
            print(opp_starter_attr)
            self.search_strategy(opp_starter_attr, team=self.team)

        if action in ['s']:
            user_input = input("\nSearch a player to see splits/strategies(ex. Luis Arraez): ")
            player_name_normalized = user_input.lower().replace(' ','')
            with open(f'players/2024/batter_metadata.json','r') as bf:
                batters = json.load(bf)
            with open(f'players/2024/pitcher_metadata.json','r') as pf:
                pitchers = json.load(pf)
            directory = f'players/2024/batter_gamelogs/'
            if any(player['fullName'] == player_name_normalized for player in pitchers.values()):
                self.splits(user_input,directory,2024,t='pitcher')
    
    
    #Lineups
    def readLineup(self):
        if self.name:
            try:
                with open(f'teams/2024/lineups/{self.team}.txt','r') as f:
                    lineup = [
                    line.replace('\n', '').lstrip() if line.replace('\n', '').startswith(' ') else line.replace('\n', '')
                    for line in f.readlines()
                    ]
                    
                return lineup
            
            except FileNotFoundError:
                 return None
            
    def getLineupIDs(self):
        with open('players/2024/batter_metadata.json','r') as f:
            batters = json.load(f)
        
        teamBattingOrder = self.readLineup()		#['Juan Soto', 'Anthony Volpe', 'Austin Wells'...]
        #For elementin batting order, tryo to match to players id
        ids = []
        
        for batter_id, data in batters.items():
            if batters[batter_id].get('fullNameAlt') in teamBattingOrder:
                ids.append(batter_id)
        
        return ids
        
        
    #26 man roster
    def getRoster(self):
        url = f"https://statsapi.mlb.com/api/v1/teams/{self.team_id}/roster"
        response = requests.get(url)
        data = response.json()
        roster = data['roster']
        
        self.position_players = []
        self.pitchers = []
        
        
        return roster
        
        
    #Bullpen Usage
    def bullpenUsage(self):
        #This method acquires, then prints the teams pitchers and their usage
       pass
        
        
        
    #Opponent
    def get_opponent(self,team):
        today = strategies.Today()
        todays_games = today.get_game_ids()	#List of game_ids

        for game_id in todays_games:
            url = f"http://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"
            response = requests.get(url)
            if response.status_code == 200:
                game_data = response.json()
                teams = game_data.get('gameData', {}).get('teams', {})
                away_team = teams.get('away', {}).get('name')
                home_team = teams.get('home', {}).get('name')
                away_team_tricode = teams.get('away', {}).get('abbreviation')
                home_team_tricode = teams.get('home', {}).get('abbreviation')
             
                try:
                    if team == away_team_tricode:
                        opp  = home_team_tricode
                        
                        return opp
                    
                    elif team == home_team_tricode:
                        opp  = away_team_tricode
                        return opp
                    else:
                        pass
                except KeyError:
                    pass
        
    def get_opp_starter(self,team):
        today = strategies.Today()
        todays_games = today.get_game_ids()	#List of game_ids
        #Find the teams game, and the corresponding opposing starter
        for game_id in todays_games:
            url = f"http://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"
            response = requests.get(url)
            if response.status_code == 200:
                game_data = response.json()
                teams = game_data.get('gameData', {}).get('teams', {})
                away_team = teams.get('away', {}).get('name')
                home_team = teams.get('home', {}).get('name')
                away_team_tricode = teams.get('away', {}).get('abbreviation')
                home_team_tricode = teams.get('home', {}).get('abbreviation')
                away_pitcher_name = game_data.get('gameData', {}).get('probablePitchers', {}).get('away', {}).get('fullName')
                home_pitcher_name = game_data.get('gameData', {}).get('probablePitchers', {}).get('home', {}).get('fullName')
                away_pitcher_id = game_data.get('gameData', {}).get('probablePitchers', {}).get('away', {}).get('id', {})
                home_pitcher_id = game_data.get('gameData', {}).get('probablePitchers', {}).get('home', {}).get('id', {})
                
                try:
                    if team == away_team_tricode:
                        opp_starter_id  = home_pitcher_id
                        
                        return opp_starter_id
                    
                    elif team == home_team_tricode:
                        opp_starter_id  = away_pitcher_id
                        
                        return opp_starter_id
                    else:
                        pass
                except KeyError:
                    pass
    
    def get_attr(self,opp_starter):
        #access a databse of each starters attrbiutes with pitcher id,
        # the value to a pitcher id will be a list of items such as this 666666: ['GB/FB>1.5', PitchingHand=Right']
        try:
            pitcher_attrs = self.PitcherAttributeDatabase[opp_starter]		#will read in the saved atrbiute json
        except KeyError:
            pitcher_attrs = 'ERA<100'
        return pitcher_attrs                                            #a string version of the attributes will be retunred, ie. 'GB/FB>1.5,PitchingHand=Right'
                                                        #It is returned to search thsi strategy for the starters opponent
        

    def process_team_data(self, df,team_combined):
        #i want to print each teams record for u2.5 'oppStarterER', and then oppStarterK records for 3+, 4+, 5+, 6+, 7+, 8+, 9+,10+.
        #And then finally print the reocrd for oppStarterH u5.5 and u4.5
        df = df[df['oppStarterP'] >= 50]
        
        
        #All of these will be appended to the same team indexed
        er = pd.Series(self.calc_stats(df,2.5,'ER'))
        k = pd.Series(self.calc_stats(df,6.5,'K'))
        k2 = pd.Series(self.calc_stats(df,5.5,'K'))
        k3 = pd.Series(self.calc_stats(df,4.5,'K'))
        h = pd.Series(self.calc_stats(df,4.5,'H'))
        h2 = pd.Series(self.calc_stats(df,5.5,'H'))
        
        
        
        team_combined.loc[len(team_combined)] = er
        team_combined.loc[len(team_combined)] = k
        team_combined.loc[len(team_combined)] = k2
        team_combined.loc[len(team_combined)] = k3
        team_combined.loc[len(team_combined)] = h
        team_combined.loc[len(team_combined)] = h2
        
        
        return team_combined
        

        
    def calc_stats(self,df,thresh,cat):
        under = len(df[df[f'oppStarter{cat}'] < thresh])
        over = len(df[df[f'oppStarter{cat}'] > thresh])
        percentage = over / (over + under) if over + under > 0 else 0
        total = over + under
        team = df['team'].iloc[0]
        formatted = {'Team': team,'Over': over,'Under': under,'Category': cat,'Threshold': thresh,'Percentage': percentage}
        return formatted
    
    def team_filters(self):
        directory = 'teams/2024/team_gamelogs'
        user_filters = input("\n\n\noperators =,>,<    cols location,ERA,GB/FB... | Enter a set of filters here to apply to all 30 MLB teams:  ")

        team_combined = pd.DataFrame(columns=['Team', 'Over', 'Under', 'Category', 'Threshold', 'Percentage'])  # Initialize as DataFrame

        for file in os.listdir(directory):
            if file.endswith('.csv') and not file.startswith('._'):
                try:
                    team_filtered_gamelog = Utils.apply_filters(os.path.join(directory, file), user_filters)
                    team_name = file[0:3].replace('_', '')
                    #print('\n\n\n', team_name)
                    df = self.process_team_data(team_filtered_gamelog,team_combined)								#???
                except IndexError:
                     pass
        team_combined_percentage_sorted = team_combined.sort_values(by=['Percentage', 'Over'], ascending=[False, True])
        
        print(user_filters)
        print(team_combined_percentage_sorted.head(25))
        print(team_combined_percentage_sorted.tail(25))
        
        
        team_combined_team_sorted = team_combined.sort_values(by='Team', ascending=True)
        print('\n'*10)
        print(user_filters)
        print(team_combined_team_sorted)

    
    def print_meta(self):
        print('\n\n',self.team,'\n')
        
    def search_team_k(self,team=None):
        filepath = 'teams/2024/team_gamelogs'
        gamelog_file = f"{filepath}/{team}_gamelogs.csv" 		#Contains the OG Gamelog creation from temp.py
        team_gamelog = pd.read_csv(gamelog_file)
        team_gamelog = team_gamelog.sort_values(by='oppStarterK', ascending=False)
        ColsToPrint = ['date','opponent','PlayerName','oppStarterK']
        team_gamelog = team_gamelog.head(10)
        
        print(team_gamelog[ColsToPrint])
        
    def process_and_display_lineup_filters(self, df, name):
        obp = round((df['isOut'] == False).sum() / len(df), 3)
        plate_appearances = len(df)
        at_bats = (plate_appearances - (df['event']  == 'Hit By Pitch').sum() - (df['event']  == 'Walk').sum() - (df['event']  == 'Sac Bunt').sum() - (df['event']  == 'Sac Fly').sum() - (df['event'] == 'Intent Walk').sum())
        batting_average = round((((df['event']  == 'Single').sum() + (df['event']  == 'Double').sum() + (df['event']  == 'Triple').sum() + (df['event']  == 'Home Run').sum())   /   at_bats), 3)
        k_pa = round((((df['event']  == 'Strikeout').sum()) / (len(df))), 3)	#strikout/pa
        pa_inning = len(df) / ((df['isOut']  == True).sum() / 3)#total plate appearances / total innings
        k_inning = pa_inning * k_pa		#Strikout rate per pa / pa/inning
        k_nine = k_inning*9
        strikeouts = (df['event']  == 'Strikeout').sum()
        slg = round((((df['event']  == 'Single').sum() + (df['event']  == 'Double').sum()*2 + (df['event']  == 'Triple').sum()*3 + (df['event']  == 'Home Run').sum()*4) / at_bats), 3)
        home_runs = (df['event'] == 'Home Run').sum()
        
        newDf = pd.DataFrame({'name': [name],
                              'obp': [obp],
                              'pa': [plate_appearances],
                              'k': [strikeouts],
                              'slg': [slg],
                              'hr': [home_runs],
                              'avg': [batting_average],
                              'K/9': [k_nine]})
        
        return newDf
                
    
    def search_strategy(self,user_strategy,team=None,batterid=None):
        years = ['2024']
        base_cols = ['date','PlayerName','PitchingHand','oppStarterP']
        all_players_df = pd.DataFrame()
        
        for year in years:
            if batterid:
                try:
                    name = self.batters[batterid]['fullNameAlt']
                    name = name.replace(' ','_')
                    filepath = f'players/{year}/PlateAppearanceLogs/batter'
                    gamelog_file = f"{filepath}/{name}_{batterid}_log.csv"
                    log = pd.read_csv(gamelog_file)
                    filters = [f.strip().replace('"', '').replace("'", "") for f in user_strategy.split(',')]
                    filtered_results = self.apply_filters(log,filters,year)
                    new_df = self.process_and_display_lineup_filters(filtered_results, name=name)
                    
                    return new_df
                except FileNotFoundError:
                    print(f'{name} FileNotFoundError. player likely has yet to play and therefore no df exists..')
            
            else:                                                                    #K
                filepath = f'teams/{year}/team_gamelogs'
                gamelog_file = f"{filepath}/{team}_gamelogs.csv" 		#Contains the OG Gamelog creation from temp.py
                team_gamelog = pd.read_csv(gamelog_file)
                
                #apply 'user_strategy' to {year}'s dataframe
                filters = [f.strip().replace('"', '').replace("'", "") for f in user_strategy.split(',')]
                filtered_team_results = self.apply_filters(team_gamelog,filters,year)
                
                markets = ['H','ER','K']  	#Unique to team  
                if markets != None:
                    for market in markets:
                        filterer = F"oppStarter{market}"
                        base_cols.append(filterer)
                        results = filtered_team_results.sort_values(by=filterer, ascending=False)
                        print(f'\n\n\n{filterer}  {team}  {user_strategy}\n',results[base_cols])
                        base_cols.remove(filterer)
                        
                
                
 
    def get_rolling_year_range(self):
        today = datetime.datetime.now()
        one_year_ago = today - datetime.timedelta(days=365)
        today_str = today.strftime('%Y-%m-%d')
        one_year_ago_str = one_year_ago.strftime('%Y-%m-%d')
        return one_year_ago_str, today_str
    


    
    def apply_filters(self, df, filters, year=None):
        rolling_average_start, rolling_average_end = self.get_rolling_year_range()
        for filter_crit in filters:
            key, operator, value = filter_crit.partition('=') if '=' in filter_crit else \
                                   filter_crit.partition('>') if '>' in filter_crit else \
                                   filter_crit.partition('<')
            key = key.strip()
            value = value.strip()

            if key == 'date':
                value = extract_year_from_date(value)  # Only convert date values for year extraction
                if value is None:
                    continue  # Skip if year extraction fails
                # If year is provided and the value is valid, filter based on the rolling average or specified year
                if year and value:
                    if year == '2023+':
                        df = df[df['date'].astype(str).between(rolling_average_start, rolling_average_end)]
                    else:
                        df = df[df['date'].astype(str).str[:4] == str(year)]
                else:
                    continue

            try:
                if operator == '=':
                    if key == 'cron':
                        user_dataset = user_dataset.tail(int(value))
                    elif value.replace('.', '', 1).isdigit():  # Simple check for numeric values
                        value = float(value)
                    elif value == 'None':  # Check if value is 'None'
                        df = df[df[key].isna()]  # Filter for NaN values
                    else:
                        df = df[df[key] == value]
                elif operator == '>':
                    df = df[df[key] > float(value)]  # Safe to convert because '>' is a numeric operation
                elif operator == '<':
                    df = df[df[key] < float(value)]  # Safe to convert because '<' is a numeric operation
            except KeyError:
                #print(f"Error: Column '{key}' not found in data. Please check your criteria.")
                continue
            except ValueError as e:
                print(f"Error processing filter '{filter_crit}': {e}")
                continue

        return df
    
    
    def access_pitcher_pitching(self,pitcher_id, pitchers):
        pitcher_id = str(pitcher_id)
        try:
            year = 2024
            pitcher_name = pitchers[pitcher_id]['PlayerName']
            player_log = pd.read_csv(f"players/{year}/pitcher_gamelogs/{pitcher_name.replace(' ','_')}_{str(pitcher_id)}.csv")
            recent_games = player_log.head(3)
            games = {}

            for i in range(3):
                game_row = recent_games.iloc[i]
                game_date = game_row['date']
                days_difference = (datetime.datetime.now() - datetime.datetime.strptime(game_date, '%Y/%m/%d')).days
                games[days_difference] = game_row['p']


            return games
        except KeyError:
            return 'No Games Played..'

    def convertTricode(self,team):
        mlb_teams = {
            'ATL': 'Braves',
            'ARI': 'Diamondbacks',
            'BAL': 'Orioles',
            'BOS': 'Red Sox',
            'CHC': 'Cubs',
            'CWS': 'White Sox',
            'CIN': 'Reds',
            'CLE': 'Guardians',
            'COL': 'Rockies',
            'DET': 'Tigers',
            'HOU': 'Astros',
            'KC': 'Royals',
            'LAA': 'Angels',
            'LAD': 'Dodgers',
            'MIA': 'Marlins',
            'MIL': 'Brewers',
            'MIN': 'Twins',
            'NYM': 'Mets',
            'NYY': 'Yankees',
            'OAK': 'Athletics',
            'PHI': 'Phillies',
            'PIT': 'Pirates',
            'SD': 'Padres',
            'SEA': 'Mariners',
            'SF': 'Giants',
            'STL': 'Cardinals',
            'TB': 'Rays',
            'TEX': 'Rangers',
            'TOR': 'Blue Jays',
            'WSH': 'Nationals'
        }
        
        return mlb_teams[team]


    def splits(self,user_input,directory,year_opt,t):
        periods = [3, 5, 7]
        years = [2024]
        with open(f'players/{year_opt}/batter_metadata.json','r') as bf:
            batters = json.load(bf)
        with open(f'players/{year_opt}/pitcher_metadata.json','r') as pf:
            pitchers = json.load(pf)
        with open('players/ids.json','r') as file:
            saved_ids = json.load(file)
        codes = ['01','02','03','04','05']
        index = 0
        
        player_name, player_id, file_path = search_player(directory, user_input)
        player_name_normalized = user_input.lower().replace(' ','')
        try:
            bbref = saved_ids[player_name_normalized]
        except KeyError:
            try:
                if isinstance(player_name,str):
                    bbref = create_player_key(player_name)
                else:
                    bbref = create_player_key_alt(user_input)
            except AttributeError:
                bbref = create_player_key_alt(user_input)
        
        div = '-'*15
        print(f"\n\n{div}\n{user_input.upper().replace(' ','')}\n")
        
        if t == 'batter':
            splits_found = False
            for code in codes:
                if splits_found == True:
                    break
                try:
                    for year in years:
                        player_splits = get_splits(bbref.replace('01',code),year=year,pitching_splits=False)
                        platoon = player_splits.loc[[('Platoon Splits', 'vs RHP'), ('Platoon Splits', 'vs LHP')]]
                        platoon = platoon.iloc[:, [2,3,5,8,13,14,15,16]]
                        platoon['H/PA'] = round(platoon['H'] / platoon['PA'], 3)
                        print(f'{year}\n',platoon)
                    splits_found = True
                except KeyError:
                    pass
                except IndexError:
                    pass
        elif t == 'pitcher':
            splits_found = False
            for code in codes:
                if splits_found == True:
                    break
                #currently does h/a 2023, splits 24
                try:
                    for year in years:
                        player_splits = get_splits(bbref.replace('01',code),year=year,pitching_splits=True)
                        platoon = player_splits[0]
                        platoon['ERA'] = round(platoon['R'] / 9, 3)
                        platoon = platoon.iloc[[5,6], [1,2,4,7,11,13,14,15]]
                        platoon['H/PA'] = round(platoon['H'] / platoon['PA'], 3)
                        print(f'\n\n{year}\n',platoon)
                    splits_found = True
                except IndexError:
                    index += 1
                    print("First time entries must be in complete format")
                    
            for pitcher_id, pitcher_data in pitchers.items():
                if pitcher_data.get('fullName','').lower() == player_name_normalized:
                    pitcher = pitcher_data
                    pitcherID = pitcher_id
                    baseName = pitcher_data['PlayerName'].lower().replace(' ','-')
            print('\n')
            print(f"PitchingHand: {pitcher['PitchingHand']}   Pitching+ {pitcher['Pitching+']}")
            keys = f"ERA: {pitcher['ERA']}   GB/FB: {pitcher['GB/FB']}   BB/9: {pitcher['BB/9']}    K/9: {pitcher['K/9']}    H/9: {pitcher['H/9']}"
            print(keys,'\n')
            
            #SIv, FBv (FAv), wSI/C, wFB/C, Pit+ CT (FC), Pit+ CB(CU)
            for key, value in pitcher.items():
                if '%' in key and key not in ['Contact%', 'Oppo%', 'Hard%', 'Pull%', 'Soft%', 'Zone%']:
                    pitch_type = key.replace('%', '').replace('2', '').replace(' ', '')
                    pitch_type_display = pitch_type if 'SI' not in pitcher else pitch_type.replace('FB', 'FA')
                    pitch_percent = f"{round(value, 3):.3f}".ljust(6)
                    if float(pitch_percent) >= 0.01:
                        pitch_type_internal = pitch_type.replace(' ', '')
                        pitch_v = f"{pitcher.get(f'v{pitch_type_internal}', 0):.1f}".ljust(6)
                        pitch_w_type = 'FB' if 'FB' in pitch_type else pitch_type
                        pitch_w = f"{pitcher.get(f'w{pitch_w_type}/C', 0):.2f}".ljust(6)
                        pitch_pit_type = 'FC' if 'CT' in pitch_type else 'CU' if 'CB' in pitch_type else 'FA' if 'FB' in pitch_type else pitch_type
                        pitch_pit = f"{pitcher.get(f'Pit+ {pitch_pit_type}', 0):.1f}"
                        pitch_pit_type_ba = 'FF' if 'FA' in pitch_pit_type else pitch_pit_type
                        avg = f"{pitcher.get(f'{pitch_pit_type_ba}_ba', 0)}"
                        print(f"{pitch_type_display}% {pitch_percent} v{pitch_type_display} {pitch_v} w{pitch_w_type}/C {pitch_w} Pit+ {pitch_pit_type} {pitch_pit}   {pitch_pit_type} .avg {avg} ")

            #Print recent pitches
            pitcher_recent = self.access_pitcher_pitching(pitcherID, pitchers)
            print('\n\nDays  Pitches\n')
            for date, pitches in pitcher_recent.items():
                print(f"{date}  {pitches}")

        if file_path:
            performance_data = {}
            df = pd.read_csv(file_path)
            print(df['team'].iloc[-1])
            for period in periods:
                hits, at_bats, average = calculate_stats(df, period)
                performance_data[period] = {'hits': hits, 'at_bats': at_bats, 'average': average}
            display_team_performance({player_name: performance_data}, periods)
            
        if index == 0:
            saved_ids[player_name_normalized] = bbref
            with open('players/ids.json','w') as file:
                json.dump(saved_ids,file)

        
        
        print(div,'\n')




