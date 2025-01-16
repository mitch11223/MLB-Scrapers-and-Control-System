
while True:
    position = input('Position')
    name = input('Name')
    if position in ['B','Batter']:
        program = input('Enter the Strategy, write code ater to decode it,\n collecting the data is the most important part')
        eye = ('Eye test')
        opp_arsenal = input("What does the opposing pitcher throw, relative to the players strengths,\n (eg. Will the pitcher stay away at all costs? or is his stuff good enough to throw anywhere")
        
        with open('players/2024/battersecrets.txt','w') as file:
            file.write(f"{position},{name},{program},{eye},{opp_arsenal}\n")
            
    if position in ['P','Pitcher']:
        split = input("K splits opp")
        Notes = input("Input opp and pitcher morale, eye test")

        with open('players/2024/pitchersecrets.txt','w') as file:
            file.write(f"{position},{name},{program},{eye},{opp_arsenal}\n")