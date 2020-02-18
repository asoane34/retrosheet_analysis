import pandas as pd 
import numpy as np

class TeamFeatureEngineer():
    def __init__(self):
        self.season_frames = []
    
    def create_features(self, df):
        #generate list of individual seasons
        year_list = list(df.season.unique())
        #iterate through seasons
        for year in year_list:
            #isolate each season as single dataframe
            single_season = df[df.season == year]
            single_season = single_season.reset_index().drop(columns = ['index'])
            #generate list of teams active during season
            team_list = list(single_season.team1.unique())
            #iterate through teams
            for team in team_list:
                #create Team object
                current_team = Team(team)
                #call class methods to create features
                current_team.get_indices(single_season)
                current_team.get_coords(single_season)
                current_team.track_season(single_season)
            self.season_frames.append(single_season)
    
    def create_frame(self):
        final_frame = pd.concat(self.season_frames, axis = 0, sort = False)
        final_frame = final_frame.reset_index().drop(columns = ['index'])
        final_frame = final_frame.sort_values(by = ['date'], axis = 0)
        return(final_frame)

        
class Team():
    def __init__(self, team_name):
        self.team_name = team_name
        self.team_indices = None
        self.distance_traveled = 0
        self.current_streak = 0
        self.current_streak_hm = 0
        self.current_streak_rd = 0
        self.record_rd = 0
        self.record_hm = 0
        self.run_differential_rd = 0
        self.run_differential_hm = 0
        self.avg_margin_rd = 0
        self.avg_margin_hm = 0
        self.current_opponent = None #only used for calculating distance travelled, will not be updated for home games
        self.n_games_played_hm = 0
        self.n_games_played_rd = 0
        self.home_lat = None
        self.home_lon = None
        self.current_lat = None #current coordinates only used when on road
        self.current_lon = None
        self.loc = None
        self.len_roadtrip = 0
        self.len_homestand = 0
        
    def track_season(self, df):
        for index in self.team_indices: 
            #home game
            if df.iloc[index]['team1'] == self.team_name:
                if self.n_games_played_hm == 0: #accounting for the first home game of the season
                    #toggle between 'H': at home and 'R': on road
                    self.loc = 'H'
                    self.len_homestand = 1
                    df.at[index, 'len_homestand'] = self.len_homestand
                    #first home game not necessarily first game, updated potential streak
                    if self.current_streak != 0:
                        df.at[index, 'current_streak_hm_tm'] = self.current_streak
                    self.n_games_played_hm += 1
                    self.distance_traveled = 0
                    game_result = df.iloc[index]['score1'] - df.iloc[index]['score2']
                    self.run_differential_hm = game_result
                    self.avg_margin_hm = game_result
                    
                    #lost first home game
                    if game_result < 0:
                        self.record_hm = -1
                        #currently on losing streak
                        if self.current_streak < 0:
                            self.current_streak += -1
                        #won or tied last game
                        else:
                            self.current_streak = -1
                        self.current_streak_hm = -1
                    
                    #tied first home game
                    elif game_result == 0:
                        self.record_hm = 0
                        self.current_streak = 0
                        self.current_streak_hm = 0
                    
                    #won first home game
                    else:
                        self.record_hm = 1
                        #currently on winning streak
                        if self.current_streak > 0:
                            self.current_streak += 1
                        #lost or tied last game
                        else:
                            self.current_streak = 1
                        self.current_streak_hm = 1
                
                #all other home games
                else:
                    #last game played at home
                    if self.loc == 'H':
                        self.len_homestand += 1
                    #last game played on road
                    else:
                        self.loc == 'H'
                        self.len_homestand = 1
                    '''
                    MAKE SURE TO UPDATE DATAFRAME OUTSIDE OF TEAM OBJECT, IF DATAFRAME IS INSIDE TEAM OBJECT,
                    FINAL MERGE WILL FAIL
                    '''
                    
                    #update dataframe with values for home team GOING INTO THE GAME, not after
                    df.at[index, 'len_homestand'] = self.len_homestand #current length of homestand 
                    df.at[index, 'current_streak_hm_tm'] = self.current_streak #home team current overall streak
                    df.at[index, 'current_streak_hm_at_hm'] = self.current_streak_hm #home team streak @ home
                    df.at[index, 'home_record_hm'] = self.record_hm #home team overall home record
                    df.at[index, 'run_differential_hm'] = self.run_differential_hm #run differential @ home
                    df.at[index, 'avg_margin_hm'] = self.avg_margin_hm #avg margin of vic/loss @ home
                    df.at[index, 'distance_traveled'] = 0
                    #update total home games played
                    self.n_games_played_hm += 1
                    #set distance traveled on current road trip to zero
                    self.distance_traveled = 0
                    #result of game
                    game_result = df.iloc[index]['score1'] - df.iloc[index]['score2']
                    #update home run differential
                    self.run_differential_hm += game_result
                    #update average home margin of victory
                    self.avg_margin_hm = self.run_differential_hm / self.n_games_played_hm
                
                    #lost home game
                    if game_result < 0: 
                        #update home record
                        self.record_hm += -1
                        
                        #on current losing streak
                        if self.current_streak < 0:
                            self.current_streak += -1
                        
                        #tied last game or was on winning streak
                        else:
                            self.current_streak = -1
                        
                        #currently on home losing streak
                        if self.current_streak_hm < 0:
                            self.current_streak_hm += -1
                        
                        #tied last home game #currently on home winning streak
                        else:
                            self.current_streak_hm = -1
                    
                    #tied home game
                    elif game_result == 0:
                        self.current_streak = 0
                        self.current_streak_hm = 0
                    
                    #won home game
                    else:
                        #update home record
                        self.record_hm += 1
                        #on winning streak
                        if self.current_streak > 0:
                            self.current_streak += 1
                        
                        #lost or tied last game
                        else:
                            self.current_streak = 1
                        
                        #currently on home winning streak
                        if self.current_streak_hm > 0:
                            self.current_streak_hm += 1
                        
                        #tied or lost last home game
                        else:
                            self.current_streak_hm = 1
            else:
                #account for first road game of season
                if self.n_games_played_rd == 0:
                    #set current location to R for road, update length of roadtrip, update number of road games played
                    self.loc = 'R'
                    self.len_roadtrip = 1
                    df.at[index, 'len_roadtrip'] = self.len_roadtrip
                    self.n_games_played_rd = 1
                    
                    #first road game not necessarily first game overall, include possible streak
                    if self.current_streak != 0:
                        df.at[index, 'current_streak_rd_tm'] = self.current_streak
                    #determine current opponent
                    self.current_opponent = df.iloc[index]['team1']
                    #determine current opponent's location / distance to game
                    self.current_lat = df.iloc[index]['primary_latitude']
                    self.current_lon = df.iloc[index]['primary_longitude']
                    self.distance_traveled = self.haversine_distance(self.home_lat, self.home_lon,\
                                                                    self.current_lat, self.current_lon)
                    #update distance traveled
                    df.at[index, 'distance_traveled'] = self.distance_traveled
                    #determine game result
                    game_result = df.iloc[index]['score2'] - df.iloc[index]['score1']
                    #update road run differential
                    self.run_differential_rd = game_result
                    #update road average margin of victory/defeat
                    self.avg_margin_rd = game_result
                    
                    #lost first road game
                    if game_result < 0:
                        #update road record
                        self.record_rd = -1
                        
                        #currently on losing streak
                        if self.current_streak < 0:
                            self.current_streak += -1
                        
                        #either tied or won last game
                        else:
                            self.current_streak = -1
                        #first game of road losing streak
                        self.current_streak_rd = -1
                    
                    #tied first road game
                    elif game_result == 0:
                        self.current_streak = 0
                        self.current_streak_rd = 0
                    
                    #won first road game
                    else:
                        self.record_rd = 1
                        
                        #on winning streak
                        if self.current_streak > 0:
                            self.current_streak += 1
                        
                        #lost or tied previously
                        else:
                            self.current_streak = 1
                        #first game of home winning streak
                        self.current_streak_rd = 1
                #all other road games
                else:
                    #update number of road games played
                    self.n_games_played_rd += 1
                    
                    #determine current opponent
                    current_opponent = df.iloc[index]['team1']
                    
                    #traveling to new opponent, on current roadtrip
                    if current_opponent != self.current_opponent and self.loc == 'R':
                        self.current_opponent = current_opponent
                        self.len_roadtrip += 1
                        new_lat = df.iloc[index]['primary_latitude']
                        new_lon = df.iloc[index]['primary_longitude']
                        distance_add = self.haversine_distance(self.current_lat, self.current_lon, \
                                                              new_lat, new_lon)
                        #update distance traveled and current coordinates
                        self.distance_traveled += distance_add
                        self.current_lat = new_lat
                        self.current_lon = new_lon
                    
                    #traveling from home to begin roadtrip
                    elif current_opponent != self.current_opponent and self.loc != 'R':
                        self.current_opponent = current_opponent
                        self.len_roadtrip = 1
                        #update current coordinates and distance traveled
                        self.current_lat = df.iloc[index]['primary_latitude']
                        self.current_lon = df.iloc[index]['primary_longitude']
                        self.distance_traveled = self.haversine_distance(self.home_lat, self.home_lon,\
                                                                        self.current_lat, self.current_lon)
                    #still on roadtrip, have not traveled
                    elif current_opponent == self.current_opponent and self.loc == 'R':
                        self.len_roadtrip += 1
                    
                    #one off case, traveling to same opponent as previous roadtrip
                    elif current_opponent == self.current_opponent and self.loc != 'R':
                        self.len_roadtrip = 1
                        self.current_lat = df.iloc[index]['primary_latitude']
                        self.current_lon = df.iloc[index]['primary_longitude']
                        self.distance_traveled = self.haversine_distance(self.home_lat, self.home_lon,\
                                                                        self.current_lat, self.current_lon)
                    #updating dataframe values
                    df.at[index, 'distance_traveled'] = self.distance_traveled
                    df.at[index, 'len_roadtrip'] = self.len_roadtrip
                    df.at[index, 'current_streak_rd_tm'] = self.current_streak
                    df.at[index, 'current_streak_rd_tm_on_rd'] = self.current_streak_rd
                    df.at[index, 'rd_record_rd'] = self.record_rd
                    df.at[index, 'run_differential_rd'] = self.run_differential_rd
                    df.at[index, 'avg_margin_rd'] = self.avg_margin_rd
                    #obtain current game result
                    game_result = df.iloc[index]['score2'] - df.iloc[index]['score1']
                    #update road run differential
                    self.run_differential_rd += game_result
                    #update road margin of victory (or loss)
                    self.avg_margin_rd = self.run_differential_rd / self.n_games_played_rd
                    
                    #lost road game
                    if game_result < 0:
                        self.record_rd += -1
                        
                        #on losing streak
                        if self.current_streak < 0:
                            self.current_streak += -1
                        #won or tied previous game
                        else:
                            self.current_streak = -1
                        
                        #on current road losing streak
                        if self.current_streak_rd < 0:
                            self.current_streak_rd += -1
                        #won/tied last road game
                        else:
                            self.current_streak_rd = -1
                    
                    #tied road game
                    elif game_result == 0:
                        self.current_streak = 0
                        self.current_streak_rd = 0
                    
                    #won road game
                    else:
                        self.record_rd += 1
                        
                        #on winning streak
                        if self.current_streak > 0:
                            self.current_streak += 0
                        #tied or lost last game
                        else:
                            self.current_streak = 1
                        
                        #on road winning streak
                        if self.current_streak_rd > 0:
                            self.current_streak_rd += 1
                        #tied or lost last road game
                        else:
                            self.current_streak_rd = 1
                                
    def get_indices(self, df):
        self.team_indices = df[(df.team1 == self.team_name) | (df.team2 == self.team_name)].index
        
    def get_coords(self, df):
        self.home_lat = df[df.team1 == self.team_name]['primary_latitude'].value_counts().idxmax()
        self.home_lon = df[df.team1 == self.team_name]['primary_longitude'].value_counts().idxmax()
    
    @staticmethod
    def haversine_distance(latitude_1, longitude_1, latitude_2, longitude_2):
        R = 6378.137
        h = np.arcsin( np.sqrt(np.sin( (np.radians(latitude_2) - np.radians(latitude_1))/2)**2 \
                           + np.cos(np.radians(latitude_1))*np.cos(np.radians(latitude_2))*\
                          np.sin( (np.radians(longitude_2) - np.radians(longitude_1))/2)**2))
        return(2 * R * h)
        
        