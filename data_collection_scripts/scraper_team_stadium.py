import json
import os
import requests
from bs4 import BeautifulSoup
import re

TEAM_CODES = ['BOS', 'NYY', 'TBD', 'TOR', 'BAL', 'MIN', 'CHW', 'CLE', 'KCR', 'DET', 'OAK', 'SEA', 'ANA', 'TEX', 'HOU',
'ATL', 'NYM', 'FLA', 'PHI', 'WSN', 'CHC', 'STL', 'CIN', 'PIT', 'MIL', 'SFG', 'SDP', 'LAD', 'ARI', 'COL']

WIKI_URL = 'https://en.wikipedia.org/wiki/'
BASE_URL = 'https://www.baseball-reference.com/teams/{}/attend.shtml'
OUTPUT_DIR = 'data/stadiums_coordinates'

class Scraper:
    """ 
    Scraper object to collect team stadium data by year from baseball-reference.com
    """
    def __init__(self, output_dir = OUTPUT_DIR, team_codes = TEAM_CODES):
        """ 
        Initialize scraper object
            Args:
                - output_dir (str): path to directory to write .json files
                - team_codes (list): list of team codes for MLB teams, used in structuring page requests
            Returns:
                - None
        """
        self.output_dir = output_dir
        self.team_codes = team_codes

    
    def scrape_stadiums(self):
        """ 
        Top level method to scrape all stadiums for each team
        """
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)
        for team_code in self.team_codes:
            team = Team(team_code)
            try:
                team.get_team_data()
            except Exception:
                print('Unable to collect data for {}'.format(team_code))
            self.write_to_file(team.team_seasons_list, team.problem_stadiums, team_code)
            print('Stadium data collected for {}'.format(team_code))
        print('Scraping Finished')            
    
    def write_to_file(self, team_list, problem_stadiums, team_code):
        file_name = self.output_dir + '/{}.json'.format(team_code)
        with open(file_name, 'w') as output_file:
            json.dump(team_list, output_file)
        problem_file_name = self.output_dir + '/{}_problems.csv'.format(team_code)
        with open(problem_file_name, 'w') as problem_file:
            for i in problem_stadiums:
                problem_file.write(i)
                problem_file.write(',\n')
            

class Team:
    """ 
    MLB team object
    """
    def __init__(self, team_code, base_url = BASE_URL):
        """ 
        Initialize Team object
            Args: 
                - team_code (str): 3 letter code for each MLB team
                - base_url (str): base URL for baseball-reference.com to structure individual team URLs
            Returns:
                - None
        """
        self.team_code = team_code
        self.base_url = base_url
        self.team_seasons_list = []
        self.stadium_dict = {}
        self.problem_stadiums = []

    def get_team_data(self):
        """ 
        Retrieve team page, parse HTML, collect team stadium data, latitude, and longitude
        """
        team_url = self.make_url(self.base_url, self.team_code)
        team_page = requests.get(team_url)
        team_soup = BeautifulSoup(team_page.content, 'html.parser')
        season_list = team_soup.find('table', {'class' : 'sortable stats_table'}).find('tbody').findAll('tr')
        for season in season_list:
            single_season = self.stadium_year_to_collect(self.team_code)
            single_season['year'] = season.find('th', {'data-stat' : 'year_ID'}).get_text()
            single_season['team'] = season.find('td', {'data-stat' : 'team_name'}).get_text()
            single_season['attendance/game'] = season.find('td', {'data-stat' : 'attendance_per_game'}).get_text()
            single_season['pitching_park_factor'] = season.find('td', {'data-stat' : 'ppf'}).get_text()
            single_season['batting_park_factor'] = season.find('td', {'data-stat' : 'bpf'}).get_text()
            stadiums = season.find('td', {'data-stat' : 'stadium'}).get_text()
            season_stadium_list = stadiums.split(', ')
            counter = 1
            for j in range(len(season_stadium_list)):
                stadium_name = ''
                stad_elements = season_stadium_list[j].split()
                for k in range(len(stad_elements)):
                    stadium_name += stad_elements[k].lower() + '_'
                counter = 1
                if stadium_name in self.stadium_dict.keys():
                    single_season['stadium_name_{}'.format(str(counter + j))] = season_stadium_list[j]
                    single_season['latitude_{}'.format(str(counter + j))] = self.stadium_dict[stadium_name].latitude
                    single_season['longitude_{}'.format(str(counter + j))] = self.stadium_dict[stadium_name].longitude
                    if self.stadium_dict[stadium_name].latitude == 'ERROR' and season_stadium_list[j] not in self.problem_stadiums:
                        self.problem_stadiums.append(season_stadium_list[j])
                    counter += 1
                else:
                    self.stadium_dict[stadium_name] = Stadium(season_stadium_list[j])
                    self.stadium_dict[stadium_name].get_coordinates()
                    single_season['stadium_name_{}'.format(str(counter + j))] = season_stadium_list[j]
                    single_season['latitude_{}'.format(str(counter + j))] = self.stadium_dict[stadium_name].latitude
                    single_season['longitude_{}'.format(str(counter + j))] = self.stadium_dict[stadium_name].longitude
                    if self.stadium_dict[stadium_name].latitude == 'ERROR' and season_stadium_list[j] not in self.problem_stadiums:
                        self.problem_stadiums.append(season_stadium_list[j])
                    counter += 1
            self.team_seasons_list.append(single_season)
    
    @staticmethod
    def make_url(base_url, team_code):
        """ 
        Factory method to structure URL for each team
            Args:
                - base_url (str): base URL for baseball-reference.com
                - team_code (str): 3 letter code for MLB team
            Returns: 
                - Individual team URL
                
        """
        return(base_url.format(team_code))
    
    @staticmethod
    def stadium_year_to_collect(team_code):
        """ 
        Factory method to initialize dictionary to store one year of team stadium data
            Args:
                - team_code (str): 3 letter code for MLB team
            Returns: 
                - Dictionary of data to collect
        """
        return(   { 'team_code' : team_code,
                    'year' : None,
                    'team' : None,
                    'attendance/game' : None,
                    'pitching_park_factor' : None,
                    'batting_park_factor' : None})


class Stadium:
    """ 
    Individual MLB stadium object
    """
    def __init__(self, stadium_name, wiki_url = WIKI_URL):
        """
        Initialize stadium object
            Args: 
                - stadium_name (str): name of the MLB stadium to collect
                - wiki_url (str): base URL for stadium wikipedia page to collect latitude and longitude
            Returns: 
                - None
        """
        self.stadium_name = stadium_name
        self.wiki_url = wiki_url
        self.latitude = None
        self.longitude = None
    
    def get_coordinates(self):
        """
        Retrieve coordinates from stadium wikipedia page
        """
        query_components = self.stadium_name.split()
        query_url = self.wiki_url
        for k in range(len(query_components) - 1):
            query_url += query_components[k]
            query_url += '_'
        query_url += query_components[-1]
        wiki_page = requests.get(query_url)
        wiki_soup = BeautifulSoup(wiki_page.content, 'html.parser')
        try:
            self.latitude = self.convert_to_decimal_format(wiki_soup.find('span', {'class' : 'latitude'}).get_text())
            self.longitude = self.convert_to_decimal_format(wiki_soup.find('span', {'class' : 'longitude'}).get_text())
            self.coordinate_checker()
        except AttributeError:
            print('The coordinates for {} cannot be found'.format(self.stadium_name))
            self.latitude = 'ERROR'
            self.longitude = 'ERROR'

    def coordinate_checker(self):
        """ 
        Determine if coordinates collected fall into an acceptable range of latitude and longitude
        """
        MAX_LON, MIN_LON, MAX_LAT, MIN_LAT = 125.0, 65.0, 50.0, 24.0
        if self.latitude > MAX_LAT or self.latitude < MIN_LAT or self.longitude > MAX_LON or self.longitude < MIN_LON:
            print('The coordinates for {} are outside of the acceptable range: {}, {}'.format(self.stadium_name, self.latitude, self.longitude))
        


    @staticmethod
    def convert_to_decimal_format(coordinate):
        """ 
        Factory method to convert coordinate from degree, minute, arcminute format into decimal format 
        so that further operations can be performed on it
            Args:
                - coordinate (str): coordinate as as string in degree, minute, arcminute form
            Returns:
                - coordinate (float): coordinate as a floating point number
        """
        degree_format = '([\d]{2,3}.[\d]{1,2}.[\d]{1,2})'
        match = re.findall(degree_format, coordinate)
        try:
            digits = re.findall('([\d]+)', match[0])
            if len(digits) != 3:
                print('The format of {} cannot be converted to decimal'.format(coordinate))
                return(coordinate)
            else:
                for i in range(len(digits)):
                    digits[i] = float(digits[i])
                return(digits[0] + digits[1]/60 + digits[2]/3600)
        except Exception:
            decimal_format = '([\d]{2,3}\.[\d]*)'
            match = re.findall(decimal_format, coordinate)
            if len(match) == 1:
                return(float(match[0]))
            else:
                print('The format of {} cannot be converted to decimal'.format(coordinate))
                return(coordinate)
       

if __name__ == '__main__':
    scraper = Scraper()
    scraper.scrape_stadiums()