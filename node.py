import requests
import json
import datetime
import os
import pandas
from teams import Teams
import time


#This class respresents a Game in the strucuture
class Node:
    def __init__(self,gameid):
        self.today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.game_id = gameid
        self.directory = f"Curve/Games/{self.today}/{self.game_id}"
        self.Notes = self.initNotes()
        self.initMeta()
    
    
    
    #Live Data
    def enterLiveScrape(self):
        url = f"http://statsapi.mlb.com/api/v1.1/game/{self.game_id}/feed/live"
        
        index_counter = None		#do not print same event multiple times
    
        
        while True:
            response = requests.get(url)
            if response.status_code == 200:
                game_data = response.json()
            
            
            #print most recent pitch/event, and have a key for user to refresh and pull again
            try:
                #if same event, dont print just pass and wait again
                #true_index ex. : 77.1
                #split true_index(.), if first half changed then tab to start a new ab
                recentEventResponse, true_index = self.getLiveData(game_data)
                
                
                if index_counter != true_index:
                    print(recentEventResponse)
                
                index_counter = true_index
                time.sleep(1)
                
            except IndexError:
                pass
            
          
            #if any key pressed, break 
        
        
    
    
    #Live Data | Helpers
    def getLiveData(self, game_data):
        atbat_index = game_data.get('liveData', {}).get('plays', {}).get('currentPlay', {}).get('atBatIndex')
        currentPlay = game_data.get('liveData', {}).get('plays', {}).get('currentPlay', {}).get('playEvents', [])[-1]
        
        index = currentPlay.get('index')
        details = currentPlay.get('details', {})
        description = details.get('description')
        isPitch = currentPlay.get('isPitch')
        
        
        true_index = f"{atbat_index}.{index}"
        if isPitch:
            pitch_type = details.get('type', {}).get('description')
            string = f"{pitch_type}  {description}"
            
            return string, true_index
        
        else:
            return description, true_index


    
    #Team Analysis
    def teamAnalysis(self):
        while True:
            print('You are in the Team Analyzer\n')
            self.printMeta()
            self.listTeamAnalysisActions()
            action = input(f'\nEnter an action (a): ')
            
            match action:
                case '':
                    break
                case 'a':
                    self.listTeamAnalysisActions()
                case 'l':
                    all_players_df = pandas.DataFrame()
                    #Lineup strategy search
                    sel = input(f'\nSelect 0:{self.home_team_name}   1: {self.away_team_name}')
                    
                    if sel in ['0','h','home','Home']:
                        user_strategy = input('\nEnter a strategy: ')
                        for batter_id in self.Home.batter_ids: 
                            new_df = self.Home.search_strategy(user_strategy, team=None, batterid=batter_id)
                            all_players_df = pandas.concat([all_players_df, new_df], ignore_index=True)
                    elif sel in ['1','a','away','Away']:
                        user_strategy = input('\nEnter a strategy: ')
                        for batter_id in self.Away.batter_ids: 
                            new_df = self.Away.search_strategy(user_strategy, team=None, batterid=batter_id)
                            all_players_df = pandas.concat([all_players_df, new_df], ignore_index=True)
                    
                    
                    print(all_players_df)
                    
                
                case 'm':
                    self.printMetaFull()		#automatic?
                case 'p':
                    #access and print player props?
                    pass
                case 's':
                    sel = input(f'\nSelect 0:{self.home_team_name}   1: {self.away_team_name}')
                    
                    if sel in ['0','h','home','Home']:
                        user_strategy = input('\nEnter a strategy: ')
                        self.Home.search_strategy(user_strategy, team=self.home_abbreviation)
                        self.last_strategy = user_strategy										#Efficiency to save strategy
                    elif sel in ['1','a','away','Away']:
                        user_strategy = input('\nEnter a strategy: ')
                        self.Away.search_strategy(user_strategy, team=self.away_abbreviation)
                        self.last_strategy = user_strategy
                case '/':
                    #self.saveStrategy(self.last_strategy)
                    pass
                    
 
        
            
    #Teams
    #def saveStrategy(self, strategy):
       #Save strategy in a strcutured way
        #easy to read in
        #Must contain [Team strategy is applied to, pitcherid/name, ]
        #Markets? Save for all 3? Specified?
        #Calculate records?
                
            
    def listTeamAnalysisActions(self):
        table = {
            ' ': 'Break',
            'a': 'Print Actions',
            'l': 'LineupStrategy (not implemented)',
            'm': 'Meta Info (auto)',
            'p': 'Props (not implemented)',
            's': 'Strategy Search',
            '/': 'Strategy Save (not implemented)'
            
        }
        print('\n\nActions..')
        for key, val in table.items():
            print(f"{key}: {val}")
        print('\n')

    
    
    #Meta
    def printMetaFull(self):				#This method prints detailed info once game is selected
        #Print lineup details, pitchers?, bullpens, weather, etc..
        print('-------------\n')
        print('GAME HOME PAGE   #Print lineup details, pitchers?, bullpens, weather, etc.. Formulate in one tensor/pull from thesere, use for ML as well?')
        print('linups on same axis, more visual?')
        print("Proccessing of evaluate_stragies instanccs. Process to tramnsform raw numbres, into actionable insights. ")
        print('Indicate wthher team has faced pitcher this year, or ever')
         
        self.Home.gatherLineup()
        self.Away.gatherLineup()
        
        #select team
        #create a way to search filters on a lineup
        #for each batter, print their average calcuclated from their PlateAppearance dataset, K/9 rate, obp%
        #dynamic w strategies entered
        print('-------------\n')
        
    def initMeta(self):
        #Collect and print meta
        url = f"http://statsapi.mlb.com/api/v1.1/game/{self.game_id}/feed/live"
        response = requests.get(url)
        game_info = ()
        
        if response.status_code == 200:
            self.game_data = response.json()
            self.teams = self.game_data.get('gameData', {}).get('teams', {})
            self.away_team_name = self.teams.get('away', {}).get('name')
            self.home_team_name = self.teams.get('home', {}).get('name')
            self.home_abbreviation = 'ARI' if self.teams.get('home', {}).get('abbreviation') == 'AZ' else self.teams.get('home', {}).get('abbreviation')
            self.away_abbreviation = 'ARI' if self.teams.get('away', {}).get('abbreviation') == 'AZ' else self.teams.get('away', {}).get('abbreviation')
            self.away_pitcher_name = self.game_data.get('gameData', {}).get('probablePitchers', {}).get('away', {}).get('fullName')
            self.home_pitcher_name = self.game_data.get('gameData', {}).get('probablePitchers', {}).get('home', {}).get('fullName')
            self.away_pitcher_id = self.game_data.get('gameData', {}).get('probablePitchers', {}).get('away', {}).get('id')
            self.home_pitcher_id = self.game_data.get('gameData', {}).get('probablePitchers', {}).get('home', {}).get('id')
            
            
            self.date = self.game_data.get('gameData', {}).get('datetime', {}).get('officialDate')
            self.time = self.game_data.get('gameData', {}).get('datetime', {}).get('time')
            self.ampm = self.game_data.get('gameData', {}).get('datetime', {}).get('ampm')
            self.teams_string = f"{self.away_team_name} @ {self.home_team_name}"
            self.pitchers_string = f"{self.away_pitcher_name}   {self.home_pitcher_name}"
            self.timestring = f"{self.time} {self.ampm}"
            self.Title = f"{self.home_team_name} @ {self.away_team_name}"
            
            

    
    def printMeta(self):
        '''print [game_time, teams, starting pitchers]'''
        
        print(self.date, self.time, self.ampm)
        print(self.teams_string)
        print(self.pitchers_string)
    
    def getActions(self):
        #This prints all possible actions
        
        table = {
            ' ': 'Break',
            '0': 'Tools  -  Use this to Search/Save Strategies, Check Props, Interact with Each Team Objects data?',
            '1': 'Record Data  -  Use these to [g: write down thoughts to compare after the game',
            '1.1': 'Print Data',
            '1.2': 'Delete Data',
            'l': 'Live Scrape',
            'x.x':'Add Others..'
            
            
        }
        print('\n\nActions..')
        for key, action in table.items():
            print(f"{key}: {action}")
        print('\n')
        
    def initTeams(self):
        #Other meta-initializations
        self.Home = Teams(team=self.home_abbreviation)
        self.Away = Teams(team=self.away_abbreviation)
        
    
    
    
    #Notes
    def initNotes(self):
        Notes = {}
        if not os.path.exists(self.directory):			#Try reading from specific file if exists, if not initialize
            os.makedirs(self.directory)
        
        try:
            with open(f"{self.directory}/Notes.json",'r') as NotesFile:
                Notes = json.load(NotesFile)
        except FileNotFoundError:
            #Notes have yet to be init. for game inst
            #Each category will hold a list of notes as they are appended
            Notes['General'] = []
        
        return Notes
    
    def recordNote(self):
        #g_This is a General Note Example!
        print("Input a note below. First carachter is flag, sep == '_'    g | '': General")
        Note = input("Input:")
        
        #Auto flag note as Genereal if not specified
        if '_' not in Note:
            Note = f"g_{Note}"
            
        category, Note = Note.split('_')[0], Note.split('_')[1]
        category = self.categoryConvert(category)
        
        self.Notes[category].append(Note)
        self.printNotes(category)
        self.saveNotes()
    
    def saveNotes(self):
        with open(f"{self.directory}/Notes.json", 'w') as NotesFile:
            json.dump(self.Notes, NotesFile, indent=4)
            
    def printNotes(self, category):
        for Note in self.Notes[category]:
            print(Note)
            
    def deleteNote(self, spec):
        category = self.categoryConvert(spec[0])
        index = int(spec[1])
        
        #Delete self.Notes[category][index]
        del self.Notes[category][index]
        self.saveNotes()		#Update notes
        print('Note Deleted..')
        
        

    def categoryConvert(self, category):	#This method simple converts a user flag (ie. 'g') to its corresponding key
        table = {
            'g': 'General',
            's': 'Statistically Inferenced'
            
        }
        
        return table[category]


    #Player Level
   