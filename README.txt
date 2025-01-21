# Cloning this repo probably will not work, as it is set up to run on my computer


#Outline: This repo allows for navigation of MLB data. It is supposed to be a barebones start/trial effort of an OOP MLB program. 
#It's goal is to collect, process, save and visualize MLB data from multiple sources packaged into one intutive program. 
#You can use the different tools to find out nuances about the game, such as which batter have the best hit records (games with a hit) against pitcher's that meet certain thresholds
#Ie (best hit record vs all RHP,K/9>9,ERA<3)
#also allows for live scraping of games as data is pushed live from MLB
#There are a lot of other things you can do too which are not mentioned


#Useful Files

#MLBImages(dir): Contains possible screenshots of some things you can do.

#Player_List.py: Main file that perpetrates the CLI interaction with MLB data. This file is run in the CL to start the program.
#MLBControlSystem.py: File that perpetrates user processing of data. Allows for searching, saving of strategies for batters and pitchers.
#Modularized_Execute.py: Main data collection and processing file. Collects and saves game json's + fangraphs data. Creates and saves player metadata jsons.
#Curve(dir): Contains Individual Pitch data and Plate Appearance logs for each even of the 2024 MLB seson
#games(dir): Collection of game json's saved from the MLB API for the 2023,2024 seasons
#execute.py: Utilizes PyBaseball and saved game json's to access, process and save MLB Data
#lineupscraper.py: Scrapes rotowire.com for up to date team lineups
#node.py: Custom Data Type to hold a game which can be cycled through by the user to see a game and its attributes. Allows for live scrpaing of games in progress.




