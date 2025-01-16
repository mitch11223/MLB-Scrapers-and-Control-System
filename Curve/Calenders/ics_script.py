from ics import Calendar
import warnings

warnings.filterwarnings("ignore")

#PRODID:-//Mariners Calendar//1.0//EN
'''
file_name = 'mlb-2024-seattle-mariners-UTC.ics'

pitchers = [
    "Bryan Woo",
    "Logan Gilbert",
    "Bryce Miller",
    "Luis Castillo",
    "George Kirby"
]

with open(file_name, 'r') as f:
    ics_content = f.read()

calendar = Calendar(ics_content)
sorted_events = sorted(calendar.events, key=lambda x: x.begin)

for i, event in enumerate(sorted_events):
    pitcher_index = i % len(pitchers)
    tentative_starter = pitchers[pitcher_index]
    
    try:
        current_summary = event.name.strip()
        new_summary = current_summary
        new_summary += f" - Tentative Starter: {tentative_starter}"    
        event.name = new_summary
        print(event.name)
    except AttributeError as e:
        continue
    


with open(file_name, 'w') as f:
    f.write(str(calendar))



print("ICS file updated successfully.")
'''


file_name = 'mlb-2024-kansas-city-royals-UTC.ics'

pitchers = [
    "Cole Ragans",
    "Alec Marsh",
    "Michael Wacha",
    "Brady Singer",
    "Seth Lugo"
]

with open(file_name, 'r') as f:
    ics_content = f.read()

calendar = Calendar(ics_content)
sorted_events = sorted(calendar.events, key=lambda x: x.begin)

for i, event in enumerate(sorted_events):
    pitcher_index = i % len(pitchers)
    tentative_starter = pitchers[pitcher_index]
    
    try:
        current_summary = event.name.strip()
        new_summary = current_summary
        new_summary += f" - Tentative Starter: {tentative_starter}"    
        event.name = new_summary
    except AttributeError as e:
        continue
    


with open(file_name, 'w') as f:
    f.write(str(calendar))


