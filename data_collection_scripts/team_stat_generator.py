import pandas as pd
import glob
import json
import re
import os
import sys

TEAM_LOC = './aggregated_event_files/team_stats_{}.csv'

HOME_COLS = ['date', 'team_code', 'opponent', 'is_doubleheader', 'is_tripleheader', 'home_OBPS',
            'home_AVG_RUNS', 'home_AVG_H', 'home_BULLPEN_ERA', 'home_BULLPEN_WHIP', 'home_BULLPEN_AVG_INNINGS',
            'home_total_OBPS', 'home_total_AVG_RUNS', 'home_total_AVG_H', 'home_total_BULLPEN_ERA',
            'home_total_BULLPEN_WHIP', 'home_total_BULLPEN_AVG_INNINGS']

ROAD_COLS = ['date', 'team_code', 'opponent', 'is_doubleheader', 'is_tripleheader', 'road_OBPS',
            'road_AVG_RUNS', 'road_AVG_H', 'road_BULLPEN_ERA', 'road_BULLPEN_WHIP', 'road_BULLPEN_AVG_INNINGS',
            'road_total_OBPS', 'road_total_AVG_RUNS', 'road_total_AVG_H', 'road_total_BULLPEN_ERA',
            'road_total_BULLPEN_WHIP', 'road_total_BULLPEN_AVG_INNINGS']

DROP_COLS = ['PA', 'AB', 'H', 'TB', 'BB', 'HBP', 'R', 'IP', 'H_', 'BB_', 'K_', 'ER_']

MERGE_KEYS = ['date', 'team_code', 'is_home', 'opponent', 'is_doubleheader', 'is_tripleheader']

class FrameUpdater():
    def __init__(self, year, team_loc = TEAM_LOC, home_cols = HOME_COLS, road_cols = ROAD_COLS, drop_cols = DROP_COLS, 
    merge_keys = MERGE_KEYS):
        self.year = year
        self.team_loc = team_loc
        self.home_cols = home_cols
        self.road_cols = road_cols
        self.drop_cols = drop_cols
        self.merge_keys = merge_keys
        self.team_frame = None
        self.all_home = None
        self.all_road = None
        self.team_names = None
        self.by_team = {}
        self.all_road_frames = []
        self.all_home_frames = []

    def aggregate_frames(self):
        self.update_frames()
        for key in self.by_team.keys():
            team_dict = self.by_team[key]
            team_dict['team_indiv'] = team_dict['team_indiv'].drop(columns = self.drop_cols)
            team_dict['team_indiv_home'] = team_dict['team_indiv_home'].drop(columns = self.drop_cols)
            team_dict['team_indiv_road'] = team_dict['team_indiv_road'].drop(columns = self.drop_cols)
            home_full = team_dict['team_indiv_home'].merge(team_dict['team_indiv'], 
                                                    how = 'left', left_on = self.merge_keys, right_on = self.merge_keys)
            home_full = home_full.drop(columns = ['is_home'])
            home_full.columns = self.home_cols
            self.all_home_frames.append(home_full)
            
            road_full = team_dict['team_indiv_road'].merge(team_dict['team_indiv'],
                                        how = 'left', left_on = self.merge_keys, right_on = self.merge_keys)
            road_full = road_full.drop(columns = ['is_home'])
            road_full.columns = self.road_cols
            self.all_road_frames.append(road_full)
        
        team1 = pd.concat(self.all_home_frames, axis = 0, sort = False)
        team2 = pd.concat(self.all_road_frames, axis = 0, sort = False)

        team1 = team1.sort_values(by = ['date']).fillna(0)
        team2 = team2.sort_values(by = ['date']).fillna(0)

        full_year = team1.merge(team2, how = 'left', left_on = ['date', 'opponent', 'is_doubleheader',
                                                            'is_tripleheader'],
                         right_on = ['date', 'team_code', 'is_doubleheader', 'is_tripleheader'])
        full_year = full_year.rename(columns = {'team_code_x' : 'home_team', 'team_code_y' : 'road_team'})
        full_year = full_year.drop(columns = ['opponent_x', 'opponent_y'])
        return(full_year)

    def update_frames(self):
        self.generate_full_frames()
        self.generate_team_frames()
        for team in self.team_names:
            full_df = self.by_team[team]['team_indiv']
            home_df = self.by_team[team]['team_indiv_home']
            road_df = self.by_team[team]['team_indiv_road']

            self.create_cols(full_df, total = True)
            self.create_cols(home_df, home = True)
            self.create_cols(road_df)
            
            for j in range(1, full_df.index.max() + 1):
                prior_games = full_df[full_df.index < j]
                self.update_team_stats(prior_games, full_df, j)
            
            for j in range(1, home_df.index.max() + 1):
                prior_games = home_df[home_df.index < j]
                self.update_road_splits(prior_games, home_df, j, home = True)
                
            #in case road/home is missing a game and dfs have different length, will update separately
            for j in range(1, road_df.index.max() + 1):
                prior_games = road_df[road_df.index < j]
                self.update_road_splits(prior_games, road_df, j)
            
            self.by_team[team]['team_indiv'] = full_df
            self.by_team[team]['team_indiv_home'] = home_df
            self.by_team[team]['team_indiv_road'] = road_df

    
    @staticmethod    
    def update_team_stats(prior_games, df, n_games):
        #calculate OBPs
        OBPS = (prior_games.TB.sum() / prior_games.AB.sum()) +\
        ((prior_games.H.sum() + prior_games.BB.sum() + prior_games.HBP.sum()) / prior_games.PA.sum())
        #calculate avg_runs / g
        AVG_R = prior_games['R'].sum() / (n_games)
        #calculate avg_hits / g
        AVG_H = prior_games['H'].sum() / (n_games)
        #bullpen_era
        B_ERA = (prior_games['ER_'].sum() / prior_games['IP'].sum()) * 9
        #bullpen whip
        B_WHIP = (prior_games['BB_'].sum() + prior_games['H_'].sum()) / prior_games['IP'].sum()
        #bullpen avg innings
        B_AVG_INN = prior_games['IP'].sum() / (n_games)
        #update main frame
        df.at[n_games, 'total_OBPS'] = OBPS
        df.at[n_games, 'total_AVG_RUNS'] = AVG_R
        df.at[n_games, 'total_AVG_H'] = AVG_H
        df.at[n_games, 'total_BULLPEN_ERA'] = B_ERA
        df.at[n_games, 'total_BULLPEN_WHIP'] = B_WHIP
        df.at[n_games, 'total_BULLPEN_AVG_INNINGS'] = B_AVG_INN
    
    @staticmethod
    def update_road_splits(prior_games, df, n_games, home = False):
        #calculate OBPs
        OBPS = (prior_games.TB.sum() / prior_games.AB.sum()) +\
        ((prior_games.H.sum() + prior_games.BB.sum() + prior_games.HBP.sum()) / prior_games.PA.sum())
        #calculate avg_runs / g
        AVG_R = prior_games['R'].sum() / (n_games)
        #calculate avg_hits / g
        AVG_H = prior_games['H'].sum() / (n_games)
        #bullpen_era
        B_ERA = (prior_games['ER_'].sum() / prior_games['IP'].sum()) * 9
        #bullpen whip
        B_WHIP = (prior_games['BB_'].sum() + prior_games['H_'].sum()) / prior_games['IP'].sum()
        #bullpen avg innings
        B_AVG_INN = prior_games['IP'].sum() / (n_games)
        #update main frame
        if home:
            df.at[n_games, 'home_OBPS'] = OBPS
            df.at[n_games, 'home_AVG_RUNS'] = AVG_R
            df.at[n_games, 'home_AVG_H'] = AVG_H
            df.at[n_games, 'home_BULLPEN_ERA'] = B_ERA
            df.at[n_games, 'home_BULLPEN_WHIP'] = B_WHIP
            df.at[n_games, 'home_BULLPEN_AVG_INNINGS'] = B_AVG_INN
        else:
            df.at[n_games, 'road_OBPS'] = OBPS
            df.at[n_games, 'road_AVG_RUNS'] = AVG_R
            df.at[n_games, 'road_AVG_H'] = AVG_H
            df.at[n_games, 'road_BULLPEN_ERA'] = B_ERA
            df.at[n_games, 'road_BULLPEN_WHIP'] = B_WHIP
            df.at[n_games, 'road_BULLPEN_AVG_INNINGS'] = B_AVG_INN

    @staticmethod
    def create_cols(df, home = False, total = False):
        if total:
            df = df.assign( total_OBPS = 0,
                            total_AVG_RUNS = 0,
                            total_AVG_H = 0,
                            total_BULLPEN_ERA = 0,
                            total_BULLPEN_WHIP = 0,
                            total_BULLPEN_AVG_INNINGS = 0)
            df['total_OBPS'] = df['total_OBPS'].astype('float32')
            df['total_AVG_RUNS'] = df['total_AVG_RUNS'].astype('float32')
            df['total_AVG_H'] = df['total_AVG_H'].astype('float32')

            df['total_BULLPEN_ERA'] = df['total_BULLPEN_ERA'].astype('float32')
            df['total_BULLPEN_WHIP'] = df['total_BULLPEN_WHIP'].astype('float32')
            df['total_BULLPEN_AVG_INNINGS'] = df['total_BULLPEN_AVG_INNINGS'].astype('float32')
        elif home:
            df = df.assign( home_OBPS = 0,
                            home_AVG_RUNS = 0,
                            home_AVG_H = 0,
                            home_BULLPEN_ERA = 0,
                            home_BULLPEN_WHIP = 0,
                            home_BULLPEN_AVG_INNINGS = 0)
            df['home_OBPS'] = df['home_OBPS'].astype('float32')
            df['home_AVG_RUNS'] = df['home_AVG_RUNS'].astype('float32')
            df['home_AVG_H'] = df['home_AVG_H'].astype('float32')

            df['home_BULLPEN_ERA'] = df['home_BULLPEN_ERA'].astype('float32')
            df['home_BULLPEN_WHIP'] = df['home_BULLPEN_WHIP'].astype('float32')
            df['home_BULLPEN_AVG_INNINGS'] = df['home_BULLPEN_AVG_INNINGS'].astype('float32')
        else:
            df = df.assign( road_OBPS = 0,
                            road_AVG_RUNS = 0,
                            road_AVG_H = 0,
                            road_BULLPEN_ERA = 0,
                            road_BULLPEN_WHIP = 0,
                            road_BULLPEN_AVG_INNINGS = 0)
            df['road_OBPS'] = df['road_OBPS'].astype('float32')
            df['road_AVG_RUNS'] = df['road_AVG_RUNS'].astype('float32')
            df['road_AVG_H'] = df['road_AVG_H'].astype('float32')

            df['road_BULLPEN_ERA'] = df['road_BULLPEN_ERA'].astype('float32')
            df['road_BULLPEN_WHIP'] = df['road_BULLPEN_WHIP'].astype('float32')
            df['road_BULLPEN_AVG_INNINGS'] = df['road_BULLPEN_AVG_INNINGS'].astype('float32')
    
    def generate_full_frames(self):
        team_loc = self.team_loc.format(str(self.year))
        
        self.team_frame = pd.read_csv(team_loc)
        self.team_frame['date'] = pd.to_datetime(self.team_frame['date'], format = '%Y-%m-%d')
        self.team_frame = self.team_frame.sort_values(by = ['team_code', 'date'])
        
        self.team_frame = self.team_frame.assign(is_doubleheader = 0,
                                       is_tripleheader = 0)

        game_counts = self.team_frame.groupby('team_code').date.value_counts()
        double_headers = game_counts[game_counts == 2]
        triple_headers = game_counts[game_counts > 2]
        
        all_double_headers = []
        for j in double_headers.index:
            all_double_headers.append(j)

        all_triple_headers = []
        for k in triple_headers.index:
            all_triple_headers.append(k)

        for index in all_double_headers:
            game_indices = self.team_frame[(self.team_frame.team_code == index[0]) & (self.team_frame.date == index[1])].index
            if len(game_indices) > 1:
                self.team_frame.at[game_indices[1], 'is_doubleheader'] = 1
            else:
                print(index)

        for index_ in all_triple_headers:
            game_indices_ = self.team_frame[(self.team_frame.team_code == index_[0]) & (self.team_frame.date == index_[1])].index
            if len(game_indices_) == 3:
                self.team_frame.at[game_indices_[1], 'is_doubleheader'] = 1
                self.team_frame.at[game_indices_[2], 'is_tripleheader'] = 1
            else:
                print(index_)
        self.all_home = self.team_frame[self.team_frame.is_home == 1].reset_index(drop = True)
        self.all_road = self.team_frame[self.team_frame.is_home == 0].reset_index(drop = True)

    def generate_team_frames(self):
        self.team_names = list(self.team_frame.team_code.unique())
        for team in self.team_names:
            i_f = {}
            i_f['team_indiv'] = self.team_frame[self.team_frame.team_code == team].reset_index(drop = True)
            i_f['team_indiv_home'] = self.all_home[self.all_home.team_code == team].reset_index(drop = True)
            i_f['team_indiv_road'] = self.all_road[self.all_road.team_code == team].reset_index(drop = True)
            self.by_team[team] = i_f


if __name__ == "__main__":
    since_1918 = []
    for year in range(1918, 2020, 1):
        updater = FrameUpdater(year)
        try:
            season_frame = updater.aggregate_frames()
            since_1918.append(season_frame)
            print('Season of {} collected'.format(year))
        except (KeyboardInterrupt, SystemExit):
            raise
        except: 
            print('There was an {} with {}'.format(sys.exc_info()[0], year))
            continue
    since_1918_df = pd.concat(since_1918, axis = 0, sort = False)
    since_1918_df = since_1918_df.sort_values(by = ['date'])
    since_1918_df.to_csv('pre_elo.csv', index = False)



            


