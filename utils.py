import pandas as pd
import json
import os
import keyboard
import sys
import time
import pandas as pd



class AnalyzeLeaguePitches:
    def findPitchesInZoneTop(df, pitch_types=None, speed_thresh=None):
        plateWidth = 1.42
        topLevel = strikeZoneTop + 0.5
        bottomLevel = strikeZoneTop - 0.3
        leftLevel = (plateWidth / 2) + 0.3
        rightLevel = (-plateWidth / 2) - 0.5

        mask = (
            (df['pZ'] <= topLevel) & (df['pZ'] >= bottomLevel) &
            (df['pX'] <= leftLevel) & (df['pX'] >= rightLevel)
        )

        if pitch_types is not None:
            mask &= df['type'].isin(pitch_types)

        if speed_thresh is not None:
            mask &= df['startSpeed'] >= speed_thresh

        masked_df = df[mask]			#Df with filters applied
        
 

        

    


class InteractiveList:
    def __init__(self, items):
        self.items = items
        self.current_index = 0

    def display_current_item(self):
        Game = self.items[self.current_index]				#Node.printMetaFull? 
        print(Game.Title, Game.timestring)

    def move_forward(self):
        self.current_index = (self.current_index + 1) % len(self.items)
        self.display_current_item()

    def move_backward(self):
        self.current_index = (self.current_index - 1) % len(self.items)
        self.display_current_item()

    def run_interactive_loop(self):
        self.display_current_item()
        while True:
            time.sleep(0.25)		#buffer
            key = keyboard.read_event(suppress=True).name
            if key == 'shift':
                self.move_backward()
            elif key == 'right shift':
                self.move_forward()
            elif key == 'q':
                print("Exiting interactive mode.")
                break
            elif key in ['caps lock']:
                return self.current_index			#Return Selected Game





class Utils():    
    def createLineup(team, players):
        players = [f for f in players.split(',')]
        with open(f'teams/2024/lineups/{team}.txt', 'w') as f:
            for player in players:
                f.write(f"{player}\n")
    
    #user_filters will be in string format.. ie. 'location=home,ERA>5'
    def apply_filters(dataset, user_filters):
        user_dataset = pd.read_csv(dataset)
        filters = [f.strip().replace('"', '').replace("'", "") for f in user_filters.split(',')]									#Converts string format to list
        #																										#Iterate through each user filter in the list
        for Filter in filters:
            #Check if there is an 'or': ...,FS%>0.1|CH%>0.1,...
            key, operator, value = Filter.partition('=') if '=' in Filter else \
                                   Filter.partition('>') if '>' in Filter else \
                                   Filter.partition('<')
            key = key.strip()																				#Eliminates extra whitespace entered by accident
            value = value.strip()
            #																					decode the operator, and apply its corresposing filter logic
            try:
                if operator == '=':
                    if key == 'cron':
                        user_dataset = user_dataset.tail(int(value))    
                    elif value.replace('.', '', 1).isdigit():  
                        value = float(value)
                    elif value == 'None':  
                        user_dataset = user_dataset[user_dataset[key].isna()]
                    else:
                        user_dataset = user_dataset[user_dataset[key] == value]
                elif operator == '>':
                    user_dataset = user_dataset[user_dataset[key] > float(value)]  
                elif operator == '<':
                    user_dataset = user_dataset[user_dataset[key] < float(value)]  
            except KeyError:
                continue
            except ValueError as e:
                print(f"Error processing filter '{filter_crit}': {e}")
                continue

        return user_dataset
    
    

    def searchPitchers(user_filters, year, ip_thresh=30):
        '''Apply filters to the keys for each player and return a DataFrame with player names and matched filter values.'''
        with open(f'players/{year}/pitcher_metadata.json', 'r') as f:
            pitchers = json.load(f)

        matching_pitchers = []
        filters = [f.strip().replace('"', '').replace("'", "") for f in user_filters.split(',')]

        for player_id, player_data in pitchers.items():
            match = True
            matched_values = {}  # To store successfully matched key values

            # Check if the pitcher meets the innings pitched threshold
            if player_data.get('IP', 0) < ip_thresh:
                continue
            
            for filter_ in filters:
                key, operator, value = filter_.partition('=') if '=' in filter_ else \
                                       filter_.partition('>') if '>' in filter_ else \
                                       filter_.partition('<')
                key = key.strip()
                value = value.strip()

                # Convert the value to float if it is numeric
                if value.replace('.', '', 1).isdigit():
                    value = float(value)

                # Apply the filter and check for matches
                if operator == '=':
                    if value == 'None':
                        if key not in player_data:  # Check if key does not exist
                            matched_values[key] = ''  # Store empty string for non-existent key
                        else:
                            match = False  # If key exists, this does not match
                            break
                    elif player_data.get(key) == value:
                        matched_values[key] = value  # Store matched value
                    else:
                        match = False
                        break
                elif operator == '>':
                    if player_data.get(key, float('-inf')) > value:
                        matched_values[key] = player_data[key]  # Store matched value
                    else:
                        match = False
                        break
                elif operator == '<':
                    if player_data.get(key, float('inf')) < value:
                        matched_values[key] = player_data[key]  # Store matched value
                    else:
                        match = False
                        break

            # If all filters matched, append the player name and matched values
            if match:
                row = {'Team': player_data.get('Team'), 'PlayerName': player_data.get('PlayerName')}
                row.update(matched_values)
                matching_pitchers.append(row)

        # Create a DataFrame from the matching pitchers
        df_matching_pitchers = pd.DataFrame(matching_pitchers)
        df_matching_pitchers.set_index('Team', inplace=True)
        df_matching_pitchers.sort_index(inplace=True)

        return df_matching_pitchers                
