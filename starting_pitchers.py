import pandas as pd 
import sys


FILE_LOC = './all_starters.csv.gz'
DROP_COLS = ['is_home', 'IP', 'H', 'BB', 'K', 'ER', 'year']
HOME_COLS = ['date', 'home_starter', 'home_team', 'road_team', 'is_doubleheader', 'is_tripleheader',
            'home_career_ERA', 'home_career_WHIP', 'home_career_AVGIP', 'home_career_ERA_AH', 
            'home_career_WHIP_AH', 'home_career_AVGIP_AH', 'home_season_ERA', 'home_season_WHIP',
            'home_season_AVGIP', 'home_season_ERA_AH', 'home_season_WHIP_AH', 'home_season_AVGIP_AH']
ROAD_COLS = ['date', 'road_starter', 'road_team', 'home_team', 'is_doubleheader', 'is_tripleheader',
            'road_career_ERA', 'road_career_WHIP', 'road_career_AVGIP', 'road_career_ERA_OR',
            'road_career_WHIP_OR', 'road_career_AVGIP_OR', 'road_season_ERA', 'road_season_WHIP',
            'road_season_AVGIP', 'road_season_ERA_OR', 'road_season_WHIP_OR', 'road_season_AVGIP_OR']
HOME_KEYS = ['date', 'home_team', 'road_team', 'is_doubleheader', 'is_tripleheader']
ROAD_KEYS = ['date', 'home_team', 'road_team', 'is_doubleheader', 'is_tripleheader']

class StartingPitcherParser():
    def __init__(self, file = FILE_LOC, drop_cols = DROP_COLS, home_cols = HOME_COLS, road_cols = ROAD_COLS, home_keys = HOME_KEYS, road_keys = ROAD_KEYS):
        self.file = file
        self.drop_cols = drop_cols
        self.home_cols = home_cols
        self.road_cols = road_cols
        self.home_keys = home_keys
        self.road_keys = road_keys
        self.all_starters = None
        self.all_home_starters = None
        self.all_road_starters = None
        self.final_frames = []
    
    def master(self):
        self.frame_prep()
        year_list = list(self.all_starters.year.unique())
        for year in year_list:
            try:
                home_starters_ = self.all_home_starters[self.all_home_starters.year == year].reset_index(drop = True)
                road_starters_ = self.all_road_starters[self.all_road_starters.year == year].reset_index(drop = True)
                all_starters_ = self.all_starters[self.all_starters.year == year].reset_index(drop = True)

                home_starters_ = self.create_cols(home_starters_, home = True)
                road_starters_ = self.create_cols(road_starters_)

                home_starters_ = self.assign_splits(home_starters_, all_starters_,  home = True)
                road_starters_ = self.assign_splits(road_starters_, all_starters_)

                home_starters_ = home_starters_.drop(columns = self.drop_cols)
                road_starters_ = road_starters_.drop(columns = self.drop_cols)

                home_starters_.columns = self.home_cols
                road_starters_.columns = self.road_cols

                final_ = home_starters_.merge(road_starters_, how = 'left', left_on = self.home_keys, right_on = self.road_keys)
                self.final_frames.append(final_)
                print('Season of {} complete'.format(year))
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                print('Problem with {}: {}'.format(year, sys.exc_info()[0]))
                continue
        try:
            complete = pd.concat(self.final_frames, axis = 0, sort = False)
            complete.to_csv('./elo_starters.csv.gz', index = False, compression = 'gzip')
            print('Complete. Look for elo_starters.csv.gz in working directory. Thanks!')
        except:
            print('There was a problem writing master file: {}'.format(sys.exc_info()[0]))

    def frame_prep(self):
        self.all_starters = pd.read_csv(self.file, compression = 'gzip')
        self.all_home_starters = self.all_starters[self.all_starters.is_home == 1].reset_index(drop = True).sort_values(by = ['date'])
        self.all_road_starters = self.all_starters[self.all_starters.is_home == 0].reset_index(drop = True).sort_values(by = ['date'])
    
    @staticmethod
    def create_cols(df, home = False):
        if home:
            df = df.assign(home_career_ERA = 0.0,
                        home_career_WHIP = 0.0,
                        home_career_AVGIP = 0.0,
                        home_career_ERA_AH = 0.0,
                        home_career_WHIP_AH = 0.0,
                        home_career_AVGIP_AH = 0.0,
                        home_season_ERA = 0.0,
                        home_season_WHIP = 0.0,
                        home_season_AVGIP = 0.0,
                        home_season_ERA_AH = 0.0,
                        home_season_WHIP_AH = 0.0,
                        home_season_AVGIP_AH = 0.0)
        else:
            df = df.assign(road_career_ERA = 0.0,
                        road_career_WHIP = 0.0,
                        road_career_AVGIP = 0.0,
                        road_career_ERA_OR = 0.0,
                        road_career_WHIP_OR = 0.0,
                        road_career_AVGIP_OR = 0.0,
                        road_season_ERA = 0.0,
                        road_season_WHIP = 0.0,
                        road_season_AVGIP = 0.0,
                        road_season_ERA_OR = 0.0,
                        road_season_WHIP_OR = 0.0,
                        road_season_AVGIP_OR = 0.0)
        return(df)

    def assign_splits(self, working, all_season, home = False):
        if home:
            for j in range(len(working)):
                pitcher = working.iloc[j]['starter_code']
                date = working.iloc[j]['date']
                starter_career = self.all_starters[(self.all_starters.date < date) & (self.all_starters.starter_code == pitcher)]
                starter_season = all_season[(all_season.date < date) & (all_season.starter_code == pitcher)]
                
                home_season = working[(working.date < date) & (working.starter_code == pitcher)]
                home_career = self.all_home_starters[(self.all_home_starters.date < date) & (self.all_home_starters.starter_code == pitcher)]
                
                working.at[j, 'home_career_ERA'] = self.ERA(starter_career)
                working.at[j, 'home_career_WHIP'] = self.WHIP(starter_career)
                working.at[j, 'home_career_AVGIP'] = self.IP(starter_career)
                working.at[j, 'home_career_ERA_AH'] = self.ERA(home_career)
                working.at[j, 'home_career_WHIP_AH'] = self.WHIP(home_career)
                working.at[j, 'home_career_AVGIP_AH'] = self.IP(home_career)
                working.at[j, 'home_season_ERA'] = self.ERA(starter_season)
                working.at[j, 'home_season_WHIP'] = self.WHIP(starter_season)
                working.at[j, 'home_season_AVGIP'] = self.IP(starter_season)
                working.at[j, 'home_season_ERA_AH'] = self.ERA(home_season)
                working.at[j, 'home_season_WHIP_AH'] = self.WHIP(home_season)
                working.at[j, 'home_season_AVGIP_AH'] = self.IP(home_season)
        else:
            for j in range(len(working)):
                pitcher = working.iloc[j]['starter_code']
                date = working.iloc[j]['date']
                starter_career = self.all_starters[(self.all_starters.date < date) & (self.all_starters.starter_code == pitcher)]
                starter_season = all_season[(all_season.date < date) & (all_season.starter_code == pitcher)]

                road_season = working[(working.date < date) & (working.starter_code == pitcher)]
                road_career = self.all_road_starters[(self.all_road_starters.date < date) & (self.all_road_starters.starter_code == pitcher)]

                working.at[j, 'road_career_ERA'] = self.ERA(starter_career)
                working.at[j, 'road_career_WHIP'] = self.WHIP(starter_career)
                working.at[j, 'road_career_AVGIP'] = self.IP(starter_career)
                working.at[j, 'road_career_ERA_OR'] = self.ERA(road_career)
                working.at[j, 'road_career_WHIP_OR'] = self.WHIP(road_career)
                working.at[j, 'road_career_AVGIP_OR'] = self.IP(road_career)
                working.at[j, 'road_season_ERA'] = self.ERA(starter_season)
                working.at[j, 'road_season_WHIP'] = self.WHIP(starter_season)
                working.at[j, 'road_season_AVGIP'] = self.IP(starter_season)
                working.at[j, 'road_season_ERA_OR'] = self.ERA(road_season)
                working.at[j, 'road_season_WHIP_OR'] = self.WHIP(road_season)
                working.at[j, 'road_season_AVGIP_OR'] = self.IP(road_season)
        return(working)

    @staticmethod            
    def ERA(df):
        if df.IP.sum() > 0:    
            return( (df.ER.sum() / df.IP.sum()) * 9)
        else:
            return(0)
    @staticmethod
    def WHIP(df):
        if df.IP.sum() > 0:
            return( (df.BB.sum() + df.H.sum()) / df.IP.sum())
        else:
            return(0)
    @staticmethod
    def IP(df):
        if len(df) != 0:
            return( df.IP.sum() / len(df))
        else:
            return(0)

if __name__ == "__main__":
    sp = StartingPitcherParser()
    sp.master()