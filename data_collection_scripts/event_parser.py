import json
import re
import pandas as pd 
import datetime
import sys
import glob
import os
''' 
RetrosheetEventFileParser is an object designed to parse Retrosheet play-by-play files into game level statistics. Each observation in the play-by-play
files represents a single play from a baseball game: a hit, stolen base, out, wild pitch, etc. There are over 13 million of these event observations,
and in order to use them to predict game outcome (winner and spread) I needed to aggregate these play observations into game observations. This
object iterates through every season and writes each season to two .csv files: One collecting all team hitting and bullpen statistics, and the other
collecting all starting pitcher statistics. 
'''
'''
Retrosheet Event Codes... These are here for reference, dict is not used in script.
COL_NAME: EVENT_CD
'''
EVENT_CODES = {0 : 'Unknown (obsolete)', 
               1 : 'None (obsolete)',
               2 : 'Generic out',
               3 : 'Strikeout',
               4 : 'Stolen Base',
               5 : 'Defensive indifference',
               6 : 'Caught stealing',
               7 : 'Pickoff error (obsolete)',
               8 : 'Pickoff',
               9 : 'Wild Pitch',
               10 : 'Passed ball',
               11 : 'Balk', 
               12 : 'Other advance/out advancing',
               13 : 'Foul error',
               14 : 'Walk',
               15 : 'Intentional walk',
               16 : 'Hit by pitch', 
               17 : 'Interference',
               18 : 'Error',
               19 : "Fielder's choice",
               20 : 'Single',
               21 : 'Double',
               22 : 'Triple',
               23 : 'Home run',
               24 : 'Missing play (obsolete)'}

'''
Load Retrosheet event file headers (scraped from Retrosheet)
'''
with open('all_event_header.json', 'r') as f:
    ALL_HEADER = json.load(f)

''' 
Specify location of Retrosheet event files csvs (parsed from .EVN to .csv by Chadwick, available via Homebrew)
'''
PATH = './parsed/'

'''
Specify output directory of 
'''
EXPORT_DIR = './aggregated_event_files/'

class RetrosheetEventFileParser():
    '''
    Parent class to parse 13 million Retrosheet event observations into game level observations for analysis
    '''
    def __init__(self, input_dir = PATH, export_dir = EXPORT_DIR, header = ALL_HEADER):
        '''
        Initialize parser class
            Args:
                - input_dir [str]: directory where Chadwick-parsed Retrosheet EVN .csvs are located
                - export_dir [str]: directory to write parsed output files to
                - header [list]: list of column names for Retrosheet Event files, scraped from Retrosheet.org
        '''
        self.input_dir = input_dir
        self.export_dir = export_dir
        self.header = header

    def parse_events(self):
        '''
        Create output directory, generate list of season event files in input directory, iterate through
        seasons and write outpute to files via child class SeasonRecreator
            Args:
                None
            Returns:
                None
        '''
        self.make_dir(self.export_dir)
        event_files = self.get_files(self.input_dir)
        for file in event_files:
            season = SeasonRecreator(file)
            try:
                season.create_season_record()
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                print('Files could not be written for {}, {}, {}'.format(file, sys.exc_info()[0], sys.exc_info()[1]))
                continue
            print('Files successfully parsed and written for {}'.format(file))

    @staticmethod
    def make_dir(export_dir):
        ''' 
        Factory method, create output directory - called in parse_events()
            Args:
                - export_dir [str]: output directory (provided in __init__)
            Returns:
                None
        '''
        if not os.path.isdir(export_dir):
            os.makedirs(export_dir)
        print('Output Directory {} created'.format(export_dir))

    @staticmethod
    def get_files(input_dir):
        ''' 
        Factory method, generate list of event .csvs
            Args:
                - input_dir [str]: input directory, location of csvs (provided in __init__)
            Returns:
                - [list] : list of file locations
        '''
        return(glob.glob('{}all*.csv'.format(input_dir)))

class SeasonRecreator(RetrosheetEventFileParser):
    ''' 
    Child class, recreate individual seasons from all*.csv files
    '''
    def __init__(self, file_name):
        ''' 
        Initialize season class
            Args:
                - file_name [str]: location of .csv file (generated by Parent class method .get_files())
        '''
        self.file_name = file_name
        self.base_df = None
        self.team_log = []
        self.starter_log = []
        self.error_log = []
        super().__init__(self)
    
    def create_season_record(self):
        ''' 
        Write collected data to .csv file
            Args:
                None
            Returns:
                None
        '''
        self.create_season()
        team_frame = pd.DataFrame(self.team_log)
        starter_frame = pd.DataFrame(self.starter_log)
        year = self.get_year(self.file_name)
        team_fn = '{}team_stats_{}.csv'.format(self.export_dir, year)
        starter_fn = '{}starter_stats_{}.csv'.format(self.export_dir, year)
        team_frame.to_csv(team_fn, header = True, index = False)
        starter_frame.to_csv(starter_fn, header = True, index = False)
        
    def create_season(self):
        ''' 
        Generate season DataFrame, iterate over all available games
            Args:
                None
            Returns:
                None
        '''
        self.base_df = pd.read_csv(self.file_name, header = None, low_memory = False)
        self.base_df.columns = self.header
        all_ids = self.base_df.GAME_ID.unique()
        for id in all_ids:
            game = GameRecreator(self.base_df, id)
            try:
                game.create_game()
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                print('There was an error {} parsing {}'.format(sys.exc_info()[0], id))
                self.error_log.append((id, sys.exc_info()[1]))
                continue
            self.team_log.append(game.home_stats)
            self.team_log.append(game.away_stats)
            self.starter_log.append(game.home_starter)
            self.starter_log.append(game.away_starter)

    @staticmethod
    def get_year(file):
        ''' 
        Factory Method, extracts year from file_name (needed for writing output files)
            Args:
                - file [str]: file_name of input .csv (provided in __init__)
            Returns:
                - [str]: 4 digit year 
        '''
        year_match = '([\d]{4})'
        return(re.findall(year_match, file)[0])    

class GameRecreator():
    ''' 
    Worker class, parses N game events in to four dictionaries: home and away team stats, home and away starter stats
    '''
    def __init__(self, base_df, game_id):
        ''' 
        Initialize game class
            Args:
                - base_df [pandas.DataFrame]: DataFrame of all season events for a given season
                - game_id [str]: Retrosheet id for game. 
                    format: '[home_team_code]{3}[date, %Y%m%d']{8}[game_number]{1}'
        '''
        self.base_df = base_df
        self.game_id = game_id
        self.game_df = None
        self.home_team = None
        self.away_team = None
        self.game_date = None
        self.home_stats = None
        self.away_stats = None
        self.home_starter = None
        self.away_starter = None
    
    def create_game(self):
        ''' 
        Create DataFrame for individual game, generate team codes and date, call parser methods
            Args:
                None
            Returns:
                None
        '''
        self.game_df = self.base_df[self.base_df.GAME_ID == self.game_id].reset_index(drop = True)
        self.home_team = self.game_df.GAME_ID.max()[0:3]
        self.away_team = self.game_df.AWAY_TEAM_ID.max()
        self.game_date = datetime.datetime.strptime(self.game_df.GAME_ID.max()[3:11], '%Y%m%d').strftime('%Y-%m-%d')
        self.collect_offensive_stats()
        self.collect_pitching()
    
    def collect_offensive_stats(self):
        '''
        Call Factory Methods to collect team offensive statistics
            Args:
                None
            Returns:
                None
        '''
        home_batting = self.initialize_batting_dict(self.game_date, self.home_team, home = True)
        away_batting = self.initialize_batting_dict(self.game_date, self.away_team)
        self.home_stats = self.get_batting(self.game_df, home_batting, home = True)
        self.away_stats = self.get_batting(self.game_df, away_batting)

    def collect_pitching(self):
        ''' 
        Call Factory Methods to collect team pitching statistics
            Args:
                None
            Returns:
                None
        '''
        home_starter = self.initialize_pitching_dict(self.game_date, self.home_team, self.away_team, home = True, starter = True)
        away_starter = self.initialize_pitching_dict(self.game_date, self.away_team, self.home_team, starter = True)
        home_relief = self.initialize_pitching_dict(self.game_date, self.home_team, self.away_team)
        away_relief = self.initialize_pitching_dict(self.game_date, self.away_team, self.home_team)
        self.home_starter, h_r = self.get_pitching(self.game_df, home_starter, home_relief, home = True)
        self.away_starter, a_r = self.get_pitching(self.game_df, away_starter, away_relief)
        self.home_stats.update(h_r)
        self.away_stats.update(a_r)


    @staticmethod
    def get_pitching(game_df, starter_dict, relief_dict, home = False):
        ''' 
        Factory method to parse game events into game pitching statistics
            Args:
                - game_df [pandas.DataFrame]: DataFrame of game events (generated by .create_game())
                - starter_dict [dict]: Initialized dictionary to record starting pitcher stats
                - relief_dict [dict]: Initalized dictionary to record relief pitcher stats
                - home [bool]: Boolean flag to indicate home or away team
            Returns: 
                - starter_dict [dict]: Dictionary of starting pitcher stats
                - relief_dict [dict]: Dictionary of relief pitcher stats
        '''
        unearned_flag = '(\(UR\))' #regex to check for unearned runners in EVENT_TX column
        removed_mid_inning = None #flag to check for inherited runners
        inherited_runners_scored = 0 #count inherited runners scored 
        ''' 
        Determine events pertaining starting pitcher and events pertaining to relief pitcher
        CAUTION: If a pitcher is removed before the game starts, Retrosheet does NOT consider the subsequent 
        starting pitcher a starting pitcher. I do, as that pitcher starts the game. Thus, the need for the 
        'de_facto_starter' below, and this pitcher will be treated as a starting pitcher.
        '''
        if home:
            starter_events = game_df[(game_df.BAT_HOME_ID == 0) & (game_df.RESP_PIT_START_FL == 'T')]
            if len(starter_events) != 0:
                relief_events = game_df[(game_df.BAT_HOME_ID == 0) & (game_df.RESP_PIT_START_FL == 'F')]
            else:
                de_facto_starter = game_df[game_df.BAT_HOME_ID == 0].iloc[0]['RESP_PIT_ID']
                starter_events = game_df[game_df.RESP_PIT_ID == de_facto_starter]
                relief_events = game_df[(game_df.BAT_HOME_ID ==0) & (game_df.RESP_PIT_ID != de_facto_starter)]
        else:
            starter_events = game_df[(game_df.BAT_HOME_ID == 1) & (game_df.RESP_PIT_START_FL == 'T')]
            if len(starter_events) != 0:
                relief_events = game_df[(game_df.BAT_HOME_ID == 1) & (game_df.RESP_PIT_START_FL == 'F')]
            else:
                de_facto_starter = game_df[game_df.BAT_HOME_ID == 1].iloc[0]['RESP_PIT_ID']
                starter_events = game_df[game_df.RESP_PIT_ID == de_facto_starter]
                relief_events = game_df[(game_df.BAT_HOME_ID ==1) & (game_df.RESP_PIT_ID != de_facto_starter)]
        
        starter_dict['starter_code'] = starter_events.iloc[0]['RESP_PIT_ID']
        #Account for complete games: No relief events
        if len(relief_events) == 0:
            starter_dict['IP'] = starter_events.iloc[-1]['INN_CT']
            starter_dict['H'] = len(starter_events[starter_events.H_FL != 0])
            starter_dict['BB'] = len(starter_events[(starter_events.EVENT_CD == 14) | (starter_events.EVENT_CD == 15)])
            starter_dict['K'] = len(starter_events[starter_events.EVENT_CD == 3])
            starter_unearned = 0 
            starter_total_runs = starter_events.EVENT_RUNS_CT.sum()
            starter_run_events = starter_events[starter_events.EVENT_RUNS_CT != 0]
            for j in range(len(starter_run_events)):
                unearned_runs = re.findall(unearned_flag, starter_run_events.iloc[j]['EVENT_TX'])
                starter_unearned += len(unearned_runs)
            starter_dict['ER'] = starter_total_runs

            for key in relief_dict.keys():
                if key == 'opponent':
                    continue
                relief_dict[key] = 0
        #account for all other games
        else:
            #determine if pitcher was removed mid inning, trigger 'removed_mid_inning' flag to check for inherited runners
            if starter_events.iloc[-1]['INN_CT'] == relief_events.iloc[0]['INN_CT']:
                removed_mid_inning = 'T'
                starter_dict['IP'] = float(format( (starter_events.iloc[-1]['INN_CT'] - 1) +\
                                                    ((starter_events.iloc[-1]['OUTS_CT'] +\
                                                    starter_events.iloc[-1]['EVENT_OUTS_CT'])/3), '.2f'))
            else:
                starter_dict['IP'] = starter_events.iloc[-1]['INN_CT']
            starter_dict['H'] = len(starter_events[starter_events.H_FL != 0])
            starter_dict['BB'] = len(starter_events[(starter_events.EVENT_CD == 14) | (starter_events.EVENT_CD == 15)])
            starter_dict['K'] = len(starter_events[starter_events.EVENT_CD == 3])
            starter_unearned = 0 
            relief_unearned = 0

            starter_total_runs = starter_events.EVENT_RUNS_CT.sum()
            starter_run_events = starter_events[starter_events.EVENT_RUNS_CT != 0]
            ''' 
            In the 160 features provided for each of the 13 million Retrosheet events, somehow EarnedRun and who the 
            EarnedRun is charged to is not among them. It is possible to find this from the given data, but it requires some 
            massaging. The remainder of this method determines how many of the scored runs were earned and who each run needs
            to be charged to. 
            '''
            for j in range(len(starter_run_events)):
                unearned_runs = re.findall(unearned_flag, starter_run_events.iloc[j]['EVENT_TX'])
                starter_unearned += len(unearned_runs)

            starter_total_runs -= starter_unearned

            if removed_mid_inning:
                starter_resp_runners = relief_events[(relief_events.RUN1_RESP_PIT_ID == starter_dict['starter_code']) |
                                        (relief_events.RUN2_RESP_PIT_ID == starter_dict['starter_code']) |
                                        (relief_events.RUN3_RESP_PIT_ID == starter_dict['starter_code'])]
                
                starter_resp_runs = starter_resp_runners[starter_resp_runners.EVENT_RUNS_CT != 0]
                
                if len(starter_resp_runs) != 0:
                    for j in range(len(starter_resp_runs)):
                        runners = starter_resp_runs.iloc[j]['EVENT_TX'].split('.')
                        if len(runners) > 1:
                            potential_runs_scored = runners[1].split(';')
                        else:
                            potential_runs_scored = runners
                        for run in potential_runs_scored:
                            if '(UR)' in run:
                                continue
                            elif 'X' in run:
                                continue
                            elif '-' not in run:
                                if run[-1] != 'H':
                                    continue
                                else:
                                    inherited_runners_scored += 1
                            else:
                                origin, dest = run.split('-')[0], run.split('-')[1]
                                if dest[0] != 'H':
                                    continue
                                elif origin == 'B':
                                    continue
                                else:
                                    base = int(origin)
                                if starter_resp_runs.iloc[j]['RUN{}_RESP_PIT_ID'.format(str(base))] == starter_dict['starter_code']:
                                    inherited_runners_scored += 1
                                else:
                                    continue
            starter_dict['ER'] = starter_total_runs + inherited_runners_scored
            relief_dict['IP'] = int(relief_events.INN_CT.max()) - starter_dict['IP']
            relief_dict['H_'] = len(relief_events[relief_events.H_FL != 0])
            relief_dict['BB_'] = len(relief_events[(relief_events.EVENT_CD == 14) | (relief_events.EVENT_CD == 15)])
            relief_dict['K_'] = len(relief_events[relief_events.EVENT_CD == 3])

            relief_total_runs = relief_events.EVENT_RUNS_CT.sum()
            relief_total_runs -= inherited_runners_scored
            relief_run_events = relief_events[relief_events.EVENT_RUNS_CT != 0]

            for j in range(len(relief_run_events)):
                unearned_runs = re.findall(unearned_flag, relief_run_events.iloc[j]['EVENT_TX'])
                relief_unearned += len(unearned_runs)
            relief_total_runs -= relief_unearned
            
            relief_dict['ER_'] = relief_total_runs
        return(starter_dict, relief_dict)

    @staticmethod
    def get_batting(game_df, data_dict, home = False):
        ''' 
        Factory method to parse game events in to team batting statistics
            Args:
                - game_df [pandas.DataFrame]: DataFrame of all game events
                - data_dict [dict]: Dictionary to record batting stats
                - home [bool]: Boolean flag to indicate home or away team
            Returns:
                - [dict]: Dictionary of team batting statistics
        '''
        if home:
            team_events = game_df[game_df.BAT_HOME_ID == 1]
        else:
            team_events = game_df[game_df.BAT_HOME_ID == 0]
        
        data_dict['PA'] = team_events.GAME_PA_CT.max() + 1
        data_dict['AB'] = len(team_events[team_events.AB_FL == 'T'])
        data_dict['H'] = len(team_events[team_events.H_FL != 0])
        data_dict['TB'] = team_events.H_FL.sum()
        data_dict['BB'] = len(team_events[(team_events.EVENT_CD == 14) | (team_events.EVENT_CD == 15)])
        data_dict['HBP'] = len(team_events[team_events.EVENT_CD == 16])
        data_dict['R'] = team_events.EVENT_RUNS_CT.sum()
        return(data_dict)


    @staticmethod
    def initialize_batting_dict(game_date, team_code, home = False):
        ''' 
        Factory method to initialize dictionary for batting stats
            Args:
                - game_date [datetime.datetime]: Datetime object, date of game
                - team_code [str]: 3 letter team code
                - home [bool]: Boolean flag to indicate home or away team
            Returns:
                - [dict]: Initialized dictionary object
        '''
        if home:
            return({'date' : game_date,
                    'team_code' : team_code,
                    'is_home' : 1,
                    'PA' : 0,
                    'AB' : 0,
                    'H' : 0,
                    'TB' : 0,
                    'BB' : 0,
                    'HBP' : 0,
                    'R' : 0})
        else:
            return({'date' : game_date,
                    'team_code' : team_code,
                    'is_home' : 0,
                    'PA' : 0,
                    'AB' : 0,
                    'H' : 0,
                    'TB' : 0,
                    'BB' : 0,
                    'HBP' : 0,
                    'R' : 0})
    @staticmethod
    def initialize_pitching_dict(game_date, team_code, opp_code, home = False, starter = False):
        ''' 
        Factory Method to initialize dictionary object for pitching stats
            Args:
                - game_date [datetime.datetime]: Datetime object, date of game
                - team_code [str]: 3 letter team code
                - opp_code [str]: 3 letter opponent team code
                - home [bool]: Boolean flag to indicate home or away team
                - starter [bool]: Boolean flag to indicate starting pitcher dict or relief pitcher dict
            Returns:
                - [dict]: Initialized dictionary object

        '''
        if home and starter:
            return({'date' : game_date,
                    'starter_code' : None,
                    'team_code' : team_code,
                    'is_home' : 1,
                    'opponent' : opp_code,
                    'IP' : 0,
                    'H' : 0,
                    'BB' : 0,
                    'K' : 0,
                    'ER' : 0})
        elif home == False and starter:
            return({'date' : game_date,
                    'starter_code' : None,
                    'team_code' : team_code,
                    'is_home' : 0,
                    'opponent' : opp_code,
                    'IP' : 0,
                    'H' : 0,
                    'BB' : 0,
                    'K' : 0,
                    'ER' : 0})
        else:
            return({'opponent' : opp_code,
                    'IP' : 0,
                    'H_' : 0,
                    'BB_' : 0,
                    'K_' : 0,
                    'ER_' : 0})

if __name__ == "__main__":
    r = RetrosheetEventFileParser()
    r.parse_events()