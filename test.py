year = '2024'
import json

with open(f'players/{year}/pitcher_metadata.json','r') as f:
    pitchers = json.load(f)
    
attrDatabase = {}

for pitcher_id, data in pitchers.items():
    pitcher_list = []
    #create a new database, keyed on pitcher id,
    #by creating attributes, from comparasion s to data['attrbiute'] in pitchers
    Data = pitchers[pitcher_id]
    
    
    way = True
    if not way:
        try:
            pitcher_list.append(f"PitchingHand={Data['PitchingHand']}")
        except KeyError:
            pass
        
        #Arsenal?
        
    if way:
        try:
            pitcher_list.append(f"PitchingHand={Data['PitchingHand']}")
        except KeyError:
            pass
        
        try:
            if Data['GB/FB'] > 1.75:
                pitcher_list.append('GB/FB>1.75')
        except KeyError:
            pass
        
        try:
            if Data['GB/FB'] < 0.8:
                pitcher_list.append('GB/FB<0.8')
        except KeyError:
            pass
        
        try:
            if Data['K/9'] > 9:
                pitcher_list.append('K/9>9')
        except KeyError:
            pass
        
        try:
            if Data['K/9'] > 8:
                pitcher_list.append('K/9>8')
        except KeyError:
            pass
        
        try:
            if Data['H/9'] < 7:
                pitcher_list.append('H/9<7')
        except KeyError:
            pass
        
        try:
            if Data['H/9'] > 9:
                pitcher_list.append('H/9>9')
        except KeyError:
            pass
        
        
        try:
            if Data['HR/9'] > 1.4:
                pitcher_list.append('HR/9>1.4')
            
            if Data['HR/9'] < 0.8:
                pitcher_list.append('HR/9<0.8')
        except KeyError:
            pass
    
    '''
    CREATE OTHER ATTRS HERE
    '''
    
    # the value to pitcher id will be a list of items such as this 666666: ['GB/FB>1.5', PitchingHand=Right']
    strategy = ','.join(pitcher_list)
    attrDatabase[pitcher_id] = strategy
    
    

save = f'players/{year}/pitcher_attributes.json'

with open(save,'w') as f:
    json.dump(attrDatabase, f)