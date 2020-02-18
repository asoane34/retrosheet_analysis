import json
import os 
from ftplib import FTP
from io import StringIO
from weather_collection_rework import WeatherCollector

OUTPUT_DIR = 'data/noaa_station_csvs/'
with open('data/federal_stations.json', 'r') as f:
    expanded_stations = json.load(f)

if __name__ == '__main__':
    collector = WeatherCollector(expanded_stations, OUTPUT_DIR)
    collector.collect_weather() 
