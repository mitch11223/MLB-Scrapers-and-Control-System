import os
import json
import pandas as pd
from datetime import datetime
import re
import time
import statsapi

class MLBStrategyManager:
    def __init__(self, filename='strategyCache/strategies.json'):
        self.filename = filename
        self.strategies = self.load_strategies()

    def load_strategies(self):
        try:
            with open(self.filename, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save_strategies(self):
        with open(self.filename, 'w') as file:
            json.dump(self.strategies, file, indent=4)

    def add_strategy(self, player, attributes, market=None, odds=None):
        strategy = {
            "attributes": attributes,
            "market": market,
            "metadata": {
                "odds": odds,
                "created_on": datetime.now().strftime('%Y-%m-%d')
            }
        }
        if player not in self.strategies:
            self.strategies[player] = {'strategies': []}
        self.strategies[player]['strategies'].append(strategy)
        self.save_strategies()
        print(f"Strategy added for {player}")
        time.sleep(1)
        self.process_strategy(player, strategy)

    def process_strategy(self, player, strategy):
        try:
            game_log_df = pd.read_csv(f'players/2023/batter_gamelogs/{player}_log.csv')
        except FileNotFoundError:
            print(f"Game log file for {player} not found.")
            return

        game_log_df = game_log_df[game_log_df['ab'] >= 3]  

        for attr, condition in strategy['attributes'].items():
            try:
                if attr == 'PitchingHand':
                    if condition == 'Left':
                        game_log_df = game_log_df[game_log_df['OpposingPitcherPitchingHand'] == 'Left']
                    elif condition == 'Right':
                        game_log_df = game_log_df[game_log_df['OpposingPitcherPitchingHand'] == 'Right']
                else:
                    operator = condition[0]
                    value = float(condition[1:])
                    if operator == '>':
                        game_log_df = game_log_df[game_log_df[attr] > value]
                    elif operator == '<':
                        game_log_df = game_log_df[game_log_df[attr] < value]
                    elif operator == '<=':
                        game_log_df = game_log_df[game_log_df[attr] <= value]
                    elif operator == '>=':
                        game_log_df = game_log_df[game_log_df[attr] >= value]
                    elif operator == '=':
                        game_log_df = game_log_df[game_log_df[attr] == value]
            except ValueError:
                pass
        successful_games_df = game_log_df[game_log_df['h'] >= 1]  # Assuming 'h' is a column for hits or similar

        total_games = len(game_log_df)
        successful_games = len(successful_games_df)
        record_percentage = (successful_games / total_games) if total_games > 0 else 0

        # Save the calculated record in the strategy
        strategy['record'] = {
            'successful_games': successful_games,
            'total_games': total_games,
            'record_percentage': record_percentage
        }

        self.save_strategies()  # Save the updated strategies to the file

    def list_strategies(self):
        if self.strategies:
            print("\nList of Strategies:")
            for player, data in self.strategies.items():
                print(f"\nStrategies for {player}:")
                for idx, strategy in enumerate(data['strategies']):
                    record = strategy.get('record', {'successful_games': 0, 'total_games': 0, 'record_percentage': 0})
                    record_display = f"{record['successful_games']}/{record['total_games']} ({record['record_percentage']*100:.2f}%)"
                    print(f"  Strategy {idx}: Attributes: {strategy['attributes']}, Market: {strategy.get('market', 'N/A')}, Odds: {strategy['metadata'].get('odds', 'N/A')}, Record: {record_display}")
        else:
            print("No strategies found.")
                

    def delete_strategy(self):
        player_name = input("Enter the player name whose strategy you want to delete: ")
        if player_name in self.strategies:
            self.list_strategies_for_player(player_name)
            strategy_index = int(input(f"Enter the index of the strategy to delete for {player_name}: "))
            try:
                del self.strategies[player_name]['strategies'][strategy_index]
                if not self.strategies[player_name]['strategies']:
                    del self.strategies[player_name]
                self.save_strategies()
                print(f"Strategy deleted for {player_name}.")
            except IndexError:
                print("Invalid strategy index.")
        else:
            print("Player not found.")

    def edit_strategy(self):
        player_name = input("Enter the player name whose strategy you want to edit: ")
        if player_name in self.strategies:
            self.list_strategies_for_player(player_name)
            strategy_index = int(input(f"Enter the index of the strategy to edit for {player_name}: "))
            try:
                strategy = self.strategies[player_name]['strategies'][strategy_index]
                attributes_input = input("Enter new attributes (key=value format, comma-separated) or press enter to keep current: ")
                if attributes_input:
                    strategy['attributes'] = parse_attributes(attributes_input)

                market = input(f"Enter new market or press enter to keep current ({strategy.get('market', 'N/A')}): ")
                if market:
                    strategy['market'] = market

                odds = input(f"Enter new odds or press enter to keep current ({strategy['metadata'].get('odds', 'N/A')}): ")
                if odds:
                    strategy['metadata']['odds'] = float(odds)

                self.save_strategies()
                print("Strategy updated successfully.")
            except IndexError:
                print("Invalid strategy index.")
        else:
            print("Player not found.")

    def list_strategies_for_player(self, player_name):
        if player_name in self.strategies:
            for idx, strategy in enumerate(self.strategies[player_name]['strategies']):
                attributes_desc = ", ".join([f"{k}: '{v}'" for k, v in strategy['attributes'].items()])
                market = strategy.get('market', 'N/A')
                odds = strategy['metadata'].get('odds', 'N/A')
                record = strategy.get('record%', 'N/A')
                print(f"  Strategy {idx}: Attributes: {attributes_desc}, Market: {market}, Odds: {odds}, Record: {record}")
        else:
            print(f"No strategies found for {player_name}.")
            
            
    def check_strategies(self):
        today = time.strftime("%Y-%m-%d")
        print(today)
        games = statsapi.schedule(start_date=today, end_date=today)
        
        for game_id in todays_games:	#must create todays_games, list of todays game_ids
            game = statsapi.get('game',{'gamePk': {game_id}})            
            #process here
            with open('testgame.json','w') as file:
                json.dump(game,file)

        
        

def parse_attributes(attributes_input):
    attributes = {}
    for attr in attributes_input.split(","):
        match = re.match(r"(.*?)(>=|<=|!=|>|<|=)(.*)", attr.strip().replace('"', ''))
        if match:
            key, operator, value = match.groups()
            attributes[key.strip()] = f"{operator}{value.strip()}"
        else:
            print(f"Invalid format for attribute: {attr}")
    return attributes

def clear_screen():
    os.system('clear')

def main():
    manager = MLBStrategyManager()
    while True:
        print("\nMLB Strategy Manager")
        print("0: List Strategies")
        print("1: Add Strategy")
        print("2: Check Strategies for Today")
        print("3: Delete a Strategy")
        print("4: Edit a Strategy")
        print("5: Exit")
        choice = input("Enter your choice: ")

        if choice == "0":
            manager.list_strategies()
        elif choice == "1":
            player = input("Enter player name: ")
            attributes_input = input("Enter strategy attributes (key=value format, comma-separated): ")
            attributes = parse_attributes(attributes_input)
            market = input("Enter market (format: 'HR>2,AVG>.300'): ")
            odds = input("Enter odds (leave blank for none): ")
            manager.add_strategy(player, attributes, market, float(odds) if odds else None)
        elif choice == "2":
            manager.check_strategies()
            # Implement or simulate checking strategies for today's games
            print("Check Strategies for Today - Functionality not implemented yet.")
        elif choice == "3":
            manager.delete_strategy()
        elif choice == "4":
            manager.edit_strategy()
        elif choice == "5":
            print("Exiting... Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")
        
        clear_screen()


'''
if __name__ == "__main__":
    main()
'''

today = time.strftime("%Y-%m-%d")
todays_games = statsapi.schedule(start_date=today, end_date=today)
for game in todays_games:
    game_id = game['game_id']
    home_pitcher = game['home_probable_pitcher']
    away_pitcher = game['away_probable_pitcher']

