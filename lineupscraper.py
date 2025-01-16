import pandas as pd
import requests
from bs4 import BeautifulSoup

#This SCript scrapes todays Batting lineups from rotowire.com

def LineupScraper():   
    url = "https://www.rotowire.com/baseball/daily-lineups.php"
    soup = BeautifulSoup(requests.get(url).content, "html.parser")

    data_pitiching = []
    data_batter = []
    team_type = ''

    for e in soup.select('.lineup__box ul li'):
        if team_type != e.parent.get('class')[-1]:
            order_count = 1
            team_type = e.parent.get('class')[-1]

        if e.get('class') and 'lineup__player-highlight' in e.get('class'):
            data_pitiching.append({
                'date': e.find_previous('main').get('data-gamedate'),
                'game_time': e.find_previous('div', attrs={'class':'lineup__time'}).get_text(strip=True),
                'PlayerName': e.a.get('title'),
                'team':e.find_previous('div', attrs={'class':team_type}).next.strip(),
                'lineup_throws':e.span.get_text(strip=True)
            })
        elif e.get('class') and 'lineup__player' in e.get('class'):
            data_batter.append({
                'date': e.find_previous('main').get('data-gamedate'),
                'game_time': e.find_previous('div', attrs={'class':'lineup__time'}).get_text(strip=True),
                'PlayerName':e.a.get('title'),
                'team':e.find_previous('div', attrs={'class':team_type}).next.strip(),
                'pos': e.div.get_text(strip=True),
                'batting_order':order_count,
                'lineup_bats':e.span.get_text(strip=True)
            })
            order_count+=1

    df_pitching = pd.DataFrame(data_pitiching)
    df_batter = pd.DataFrame(data_batter)
    

    
    return df_batter

    
