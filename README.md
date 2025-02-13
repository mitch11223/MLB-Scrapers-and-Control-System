# MLB Data Navigation Project

**Warning**: Cloning this repo might not work as intended since it's configured to run on my personal setup.

## Outline
This repository provides a basic, object-oriented framework for navigating MLB data. It's an initial trial to:
- Collect, process, save, and visualize MLB data from various sources into an intuitive program.
- Enable users to explore game nuances, like identifying batters with the best hit records against pitchers meeting specific criteria (e.g., best hit record vs. all RHP with K/9 > 9, ERA < 3).
- Support live scraping of games as data is updated by MLB.

This project offers numerous possibilities beyond what's explicitly listed here.

## Useful Files and Directories

### Directories
- **MLBImages**: Contains example screenshots of functionalities.
- **Curve**: Stores individual pitch data and plate appearance logs for each event of the 2024 MLB season.
- **games**: Holds JSON files of game data from MLB API for the 2023 and 2024 seasons.

### Python Files
- **Player_List.py**: 
  - The main CLI interaction file. Run this to start the program.

- **MLBControlSystem.py**: 
  - Manages user data processing, including searching and saving strategies for batters and pitchers.

- **Modularized_Execute.py**: 
  - Central file for data collection and processing. It collects and saves game JSONs, alongside Fangraphs data, creating player metadata JSONs.

- **execute.py**: 
  - Uses PyBaseball and saved game JSONs to access, process, and save MLB data.

- **lineupscraper.py**: 
  - Scrapes rotowire.com for the latest team lineups.

- **node.py**: 
  - A custom data type representing a game, allowing the user to cycle through games and their attributes, including live scraping of games in progress.

## Note
Given the project's dependence on local configurations, setting up this project on another machine might require adjustments or might not function as expected out-of-the-box.
