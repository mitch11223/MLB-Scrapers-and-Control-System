import os
import pandas as pd
import json
import requests

class Weather:
    def __init__(self):
        self.API_key = 'db581c2c88d875e38fc9c5c86668a796'
    
    def search_weatherLive(self, city=None):
        lat, lon = self.search_city(city)
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.API_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
        
        humidity = data['main'].get('humidity')
        print(f"{city} humidity: {humidity}")
    
    def search_city(self, city):
        #Returns latitude and longitude of given city
        #Dict of ballpark lat, lon
        ballparks = {
            'Baltimore': '39.284176,-76.622368'
        }
        latlon_string = ballparks[city]
        lat, lon = latlon_string.split(',')
        return lat, lon



x = Weather()
x.search_weatherLive('Baltimore')

#NonLive?