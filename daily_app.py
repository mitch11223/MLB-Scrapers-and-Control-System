#this is the flask file
import strategies
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    Day = strategies.Today()
    games = Day.get_game_ids()
    game_info = []
    for game_id in games:
        game_info.append(Day.get_meta(game_id))
    return render_template('index.html', games=game_info)


if __name__ == '__main__':
    app.run(debug=True)