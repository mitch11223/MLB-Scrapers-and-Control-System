import json
import pandas as pd

class Player():
    def __init__(self, playerID, isPitcher=None):
        self.playerID = playerID
        self.isPitcher = isPitcher
        self.Dict = self.acquireDict()
        
    def acquireDict(self):
        if self.isPitcher:
            with open('players/2024/pitcher_metadata.json','r') as f:
                pitchers = json.load(f)
            
            pitcher = pitchers[self.playerID]
            return pitcher
        
        else:
            with open('players/2024/batter_metadata.json','r') as f:
                batters = json.load(f)
                
            batter = batters[self.playerID]
            return batter