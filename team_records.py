from utils import Utils
import pandas as pd
import os

class TeamRecords:
    
    #Methods
    def ER(self, user_filters):
        team_combined = pd.DataFrame(columns=['Team', 'Over', 'Under', 'Category', 'Threshold', 'Percentage'])
        file_path = 'teams/2024/team_gamelogs'
        
        for file in os.listdir(file_path):
            if file.endswith('.csv') and not file.startswith('._'):
                try:
                    team_filtered_gamelog = Utils.apply_filters(os.path.join(file_path, file), user_filters)
                    team_name = file[0:3].replace('_', '')
                    df = self.process_team_data('ER',team_filtered_gamelog, team_combined)
                    
                except IndexError:
                     pass
        team_combined = team_combined.set_index('Team')
        return team_combined.sort_values(by='Percentage', ascending=False)
            
    
    def ERA(self, user_filters):
        '''This method caluclates and reutnrs the ERA against he team petaining to the user_filters entered'''
        
        team_combined = pd.DataFrame(columns=['Team', 'ERA', 'Games'])			#avg? slg? obp?...
        file_path = 'teams/2024/team_gamelogs'
        
        for file in os.listdir(file_path):
            if file.endswith('.csv') and not file.startswith('._'):
                try:
                    team_filtered_gamelog = Utils.apply_filters(os.path.join(file_path, file), user_filters)
                    team_name = file[0:3].replace('_', '')
                    df = self.process_team_data('ERA',team_filtered_gamelog, team_combined)
                    
                except IndexError:
                     pass
        team_combined = team_combined.set_index('Team')
        return team_combined.sort_values(by='ERA', ascending=True)
            
    
    
    
    def calc_stats(self,df,thresh,cat):
        '''This method calculates and formattes by category'''
        '''input: Dataframe, threshold and category'''
        
        under = len(df[df[f'oppStarter{cat}'] < thresh])
        over = len(df[df[f'oppStarter{cat}'] > thresh])
        percentage = over / (over + under) if over + under > 0 else 0
        total = over + under
        team = df['team'].iloc[0]
        formatted = {'Team': team,'Over': over,'Under': under,'Category': cat,'Threshold': thresh,'Percentage': percentage}
        return formatted
    
    
    def process_team_data(self, Type, df, team_combined):
        #This method adds rows to the complete league df
        df = df[df['oppStarterP'] >= 50]
        
        
        if Type == 'ER':
            er = pd.Series(self.calc_stats(df,2.5,'ER'))
            team_combined.loc[len(team_combined)] = er
            
        if Type == 'ERA':
            era = pd.Series({'Team': df['team'].iloc[0], 'ERA': round(df['oppStarterER'].mean(), 2), 'Games': len(df)})
            team_combined.loc[len(team_combined)] = era
        
        return team_combined

