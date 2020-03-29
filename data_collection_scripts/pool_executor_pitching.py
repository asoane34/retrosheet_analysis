import pandas as pd 
import concurrent.futures
import sys
import os

OUTPUT_DIR = './elo_starter/'
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

def exec_fn(year, all_starters, all_home_starters, all_road_starters, drop_cols = DROP_COLS, home_cols = HOME_COLS, 
road_cols = ROAD_COLS, home_keys = HOME_KEYS, road_keys = ROAD_KEYS, output_dir = OUTPUT_DIR):   
    
    home_starters_ = all_home_starters[all_home_starters.year == year].reset_index(drop = True)
    road_starters_ = all_road_starters[all_road_starters.year == year].reset_index(drop = True)
    all_starters_ = all_starters[all_starters.year == year].reset_index(drop = True)

    home_starters_ = create_cols(home_starters_, home = True)
    road_starters_ = create_cols(road_starters_)

    home_starters_ = assign_splits(home_starters_, all_starters, all_starters_, all_home_starters, all_road_starters, home = True)
    road_starters_ = assign_splits(road_starters_, all_starters, all_starters_, all_home_starters, all_road_starters)

    home_starters_ = home_starters_.drop(columns = drop_cols)
    road_starters_ = road_starters_.drop(columns = drop_cols)

    home_starters_.columns = home_cols
    road_starters_.columns = road_cols

    final_ = home_starters_.merge(road_starters_, how = 'left', left_on = home_keys, right_on = road_keys)
    final_.to_csv('{}{}.csv'.format(output_dir, year), index = False)
    print('{} written'.format(year))
    

def assign_splits(working, all_starters, all_season, all_home, all_road, home = False):
    if home:
        for j in range(len(working)):
            pitcher = working.iloc[j]['starter_code']
            date = working.iloc[j]['date']
            starter_career = all_starters[(all_starters.date < date) & (all_starters.starter_code == pitcher)]
            starter_season = all_season[(all_season.date < date) & (all_season.starter_code == pitcher)]
            
            home_season = working[(working.date < date) & (working.starter_code == pitcher)]
            home_career = all_home[(all_home.date < date) & (all_home.starter_code == pitcher)]
            
            working.at[j, 'home_career_ERA'] = ERA(starter_career)
            working.at[j, 'home_career_WHIP'] = WHIP(starter_career)
            working.at[j, 'home_career_AVGIP'] = IP(starter_career)
            working.at[j, 'home_career_ERA_AH'] = ERA(home_career)
            working.at[j, 'home_career_WHIP_AH'] = WHIP(home_career)
            working.at[j, 'home_career_AVGIP_AH'] = IP(home_career)
            working.at[j, 'home_season_ERA'] = ERA(starter_season)
            working.at[j, 'home_season_WHIP'] = WHIP(starter_season)
            working.at[j, 'home_season_AVGIP'] = IP(starter_season)
            working.at[j, 'home_season_ERA_AH'] = ERA(home_season)
            working.at[j, 'home_season_WHIP_AH'] = WHIP(home_season)
            working.at[j, 'home_season_AVGIP_AH'] = IP(home_season)
    else:
        for j in range(len(working)):
            pitcher = working.iloc[j]['starter_code']
            date = working.iloc[j]['date']
            starter_career = all_starters[(all_starters.date < date) & (all_starters.starter_code == pitcher)]
            starter_season = all_season[(all_season.date < date) & (all_season.starter_code == pitcher)]

            road_season = working[(working.date < date) & (working.starter_code == pitcher)]
            road_career = all_road[(all_road.date < date) & (all_road.starter_code == pitcher)]

            working.at[j, 'road_career_ERA'] = ERA(starter_career)
            working.at[j, 'road_career_WHIP'] = WHIP(starter_career)
            working.at[j, 'road_career_AVGIP'] = IP(starter_career)
            working.at[j, 'road_career_ERA_OR'] = ERA(road_career)
            working.at[j, 'road_career_WHIP_OR'] = WHIP(road_career)
            working.at[j, 'road_career_AVGIP_OR'] = IP(road_career)
            working.at[j, 'road_season_ERA'] = ERA(starter_season)
            working.at[j, 'road_season_WHIP'] = WHIP(starter_season)
            working.at[j, 'road_season_AVGIP'] = IP(starter_season)
            working.at[j, 'road_season_ERA_OR'] = ERA(road_season)
            working.at[j, 'road_season_WHIP_OR'] = WHIP(road_season)
            working.at[j, 'road_season_AVGIP_OR'] = IP(road_season)
    return(working)

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

def ERA(df):
    if df.IP.sum() > 0:    
        return( (df.ER.sum() / df.IP.sum()) * 9)
    else:
        return(0)

def WHIP(df):
    if df.IP.sum() > 0:
        return( (df.BB.sum() + df.H.sum()) / df.IP.sum())
    else:
        return(0)

def IP(df):
    if len(df) != 0:
        return( df.IP.sum() / len(df))
    else:
        return(0)

if __name__ == "__main__":
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    all_starters_main = pd.read_csv('./all_starters.csv.gz', compression = 'gzip')
    all_home_starters_main = all_starters_main[all_starters_main.is_home == 1].reset_index(drop = True).sort_values(by = ['date'])
    all_road_starters_main = all_starters_main[all_starters_main.is_home == 0].reset_index(drop = True).sort_values(by = ['date'])

    YEAR_LIST = list(all_starters_main.year.unique())

    with concurrent.futures.ProcessPoolExecutor(max_workers = 6) as executor:
        for year in YEAR_LIST:
            executor.submit(exec_fn, year, all_starters_main, all_home_starters_main, all_road_starters_main)

