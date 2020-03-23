'''
This is a rework of the Retrosheet event_parser file... One of the major issues 
I've faced in modeling is the collinearity of the features. The features
are highly collinear, but removing features has led to an untenably high loss
of information. To counteract this, I have decided that I need to come up with 
an Offensive and Pitcher rating system. (I'm also currently in quarantine and 
bored out of my skull, yes). To do this, I am extracting ADVANCED metrics 
(shout out the Train) from the Retrosheet play-by-play files... Also
adding multiprocessing capability which was missing in version 1
'''

from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor
import sys
import os
import json
import pickle
import glob
import datetime
import pandas as pd
import re

EVENT_HEADER = r"./intermediate_data/all_event_header.json"

INPUT = r"./parsed/all*.csv"

OUTPUT_DIR = r"./adv_metrics/"

@dataclass
class EventParser():
    input_dir: str = INPUT
    output_dir: str = OUTPUT_DIR
    event_header: str = EVENT_HEADER
    n_jobs: int = None
    event_headers: list = field(default_factory = list)
    all_games: list = field(default_factory = list)
    to_csv: bool = True
    _zip: bool = True
    to_json: bool = False
    to_pickle: bool = False

    def parse_events(self):

        self._prep()

        all_files = glob.glob(self.input_dir)

        for file in all_files:
            
            try:
            
                season = file.split("all")[1][0:4]

                season_df = pd.read_csv(file, low_memory = False, header = None)

                season_df.columns = self.event_headers

                all_games = season_df.GAME_ID.unique()

                season_list = []

                with ProcessPoolExecutor(max_workers = self.n_jobs) as executor:

                    for game in all_games:

                        game_df = season_df[season_df.GAME_ID == game].reset_index(drop = True)

                        season_list.append(executor.submit(self.recreate_game, game_df, game))

                season_list = [i.result() for i in season_list]

                self.all_games += season_list

                print("All data collected for {} season".format(season))

            except (SystemExit, KeyboardInterrupt):

                raise

            except:

                print("There was a problem with {}: {}".format(season, sys.exc_info()[0]))

                continue

        if self.to_csv:

            try:

                final = pd.DataFrame(self.all_games)

                if self._zip:

                    final.to_csv("{}raw_game_data.csv.gz".format(self.output_dir), 
                    index = False, compression = "gzip")

                else:

                    final.to_csv("{}raw_game_data.csv".format(self.output_dir),
                    index = False)

                print("Data successfully written to .CSV")

            except (SystemExit, KeyboardInterrupt):

                raise

            except:

                print("Encountered the following error writing file to .csv: {}".format(sys.exc_info()[0]))

        if self.to_json:

            try:

                with open("{}raw_game_data.json".format(self.output_dir), "w+") as f:

                    json.dump(self.all_games, f)

                    print("Data successfully written to JSON")

            except (SystemExit, KeyboardInterrupt):

                raise
            
            except:

                print("Encountered the following error writing file to .json: {}".format(sys.exc_info()[0]))

        if self.to_pickle:

            try:

                with open("{}raw_game_data.pk", "wb") as f:

                    pickle.dump(self.all_games, f)

                    print("Data successfully pickled")

            except (SystemExit, KeyboardInterrupt):

                raise

            except:

                print("Encountered the following error writing file to .pk: {}".format(sys.exc_info()[0]))

    
    def _prep(self):

        if not os.path.exists(self.output_dir):

            os.makedirs(self.output_dir)

        with open(self.event_header, "r+") as f:

            self.event_headers = json.load(f)
    
    @staticmethod
    def recreate_game(game_df, game_id):

        unearned_flag = r"(\(UR\))"
        
        game_master = {}

        game_master["date"] = datetime.datetime.strptime(game_id[3:11], "%Y%m%d").strftime("%Y-%m-%d")

        game_master["home_team"] = game_id[0:3]

        game_master["road_team"] = game_df.iloc[0]["AWAY_TEAM_ID"]

        if game_id[11] == "2":

            game_master["is_doubleheader"] = 1

        elif game_id[11] == "3":

            game_master["is_tripleheader"] = 1

        else:

            game_master["is_doubleheader"] = 0 

            game_master["is_tripleheader"] = 0

        prefixes = ["home_", "road_"]

        for prefix in prefixes:

            if prefix == "home_":

                team_events = game_df[game_df.BAT_HOME_ID == 1]

                alt = "road_"

            else:

                team_events = game_df[game_df.BAT_HOME_ID == 0]

                alt = "home_"

            #BEGIN OFFENSIVE COLLECTION

            game_master[prefix + "PA"] = team_events.GAME_PA_CT.max() + 1

            game_master[prefix + 'AB'] = len(team_events[team_events.AB_FL == 'T'])

            game_master[prefix + 'H'] = len(team_events[team_events.H_FL != 0])

            game_master[prefix + "1B"] = len(team_events[team_events.EVENT_CD == 20])

            game_master[prefix + "2B"] = len(team_events[team_events.EVENT_CD == 21])

            game_master[prefix + "3B"] = len(team_events[team_events.EVENT_CD == 22])

            game_master[prefix + "HR"] = len(team_events[team_events.EVENT_CD == 23])

            game_master[prefix + 'TB'] = team_events.H_FL.sum()

            game_master[prefix + 'BB'] = len(team_events[team_events.EVENT_CD == 14])

            game_master[prefix + 'IBB'] = len(team_events[team_events.EVENT_CD == 15])

            game_master[prefix + 'HBP'] = len(team_events[team_events.EVENT_CD == 16])

            game_master[prefix + 'R'] = team_events.EVENT_RUNS_CT.sum()

            #BEGIN PITCHING COLLECTION 

            starter_events = team_events[team_events.RESP_PIT_START_FL == "T"]

            if len(starter_events) != 0:

                relief_events = team_events[team_events.RESP_PIT_START_FL != "T"]

            else:

                de_facto_starter = team_events.iloc[0]["RESP_PIT_ID"]

                starter_events = team_events[team_events.RESP_PIT_ID == de_facto_starter]

                relief_events = team_events[team_events.RESP_PIT_ID != de_facto_starter]

            game_master[alt + "starter"] = starter_events.iloc[0]["RESP_PIT_ID"]

            game_master[alt + "starter_H"] = len(starter_events[starter_events.H_FL != 0])

            game_master[alt + "starter_HR"] = len(starter_events[starter_events.EVENT_CD == 23])

            game_master[alt + "starter_BB"] = len(starter_events[starter_events.EVENT_CD == 14])

            game_master[alt + "starter_IBB"] = len(starter_events[starter_events.EVENT_CD == 15])

            game_master[alt + "starter_HBP"] = len(starter_events[starter_events.EVENT_CD == 16])

            game_master[alt + "starter_K"] = len(starter_events[starter_events.EVENT_CD == 3])

            if len(relief_events) == 0:

                game_master[alt + "starter_IP"] = starter_events.iloc[-1]["INN_CT"]

                starter_unearned = 0

                starter_total_runs = starter_events.EVENT_RUNS_CT.sum()
                
                starter_run_events = starter_events[starter_events.EVENT_RUNS_CT != 0]
                
                for j in range(len(starter_run_events)):
                
                    unearned_runs = re.findall(unearned_flag, starter_run_events.iloc[j]['EVENT_TX'])
                
                    starter_unearned += len(unearned_runs)

                starter_total_runs -= starter_unearned

                game_master[alt + "starter_ER"] = starter_total_runs

                relief_cols = ["relief_IP", "relief_H", "relief_HR", "relief_BB", "relief_BB", "relief_IBB", "relief_HBP",
                "relief_K", "relief_ER"]

                for col in relief_cols:

                    game_master[alt + col] = 0

            else:

                inherited_runners_scored = 0

                removed_mid_inning = None

                if starter_events.iloc[-1]["INN_CT"] == relief_events.iloc[0]["INN_CT"]:

                    removed_mid_inning = "T"

                    game_master[alt + 'starter_IP'] = float(format( (starter_events.iloc[-1]['INN_CT'] - 1) +\
                                                        ((starter_events.iloc[-1]['OUTS_CT'] +\
                                                        starter_events.iloc[-1]['EVENT_OUTS_CT'])/3), '.2f'))

                else:

                    game_master[alt + "starter_IP"] = starter_events.iloc[-1]["INN_CT"]

                starter_unearned = 0

                relief_unearned = 0

                starter_total_runs = starter_events.EVENT_RUNS_CT.sum()

                starter_run_events = starter_events[starter_events.EVENT_RUNS_CT != 0]

                for j in range(len(starter_run_events)):

                    unearned_runs = re.findall(unearned_flag, starter_run_events.iloc[j]['EVENT_TX'])

                    starter_unearned += len(unearned_runs)

                starter_total_runs -= starter_unearned

                if removed_mid_inning:

                    starter_resp_runners = relief_events[(relief_events.RUN1_RESP_PIT_ID == game_master[alt + "starter"]) |
                                            (relief_events.RUN2_RESP_PIT_ID == game_master[alt + "starter"]) |
                                            (relief_events.RUN3_RESP_PIT_ID == game_master[alt + "starter"])]
                    
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
                            
                                    if starter_resp_runs.iloc[j]['RUN{}_RESP_PIT_ID'.format(str(base))] == game_master[alt + "starter"]:
                            
                                        inherited_runners_scored += 1
                            
                                    else:
                            
                                        continue

                game_master[alt + "starter_ER"] = starter_total_runs + inherited_runners_scored

                game_master[alt + "relief_IP"] = int(relief_events.INN_CT.max()) - game_master[alt + "starter_IP"]

                game_master[alt + "relief_H"] = len(relief_events[relief_events.H_FL != 0])

                game_master[alt + "relief_HR"] = len(relief_events[relief_events.EVENT_CD == 23])

                game_master[alt + "relief_BB"] = len(relief_events[relief_events.EVENT_CD == 14])

                game_master[alt + "relief_IBB"] = len(relief_events[relief_events.EVENT_CD == 15])

                game_master[alt + "relief_HBP"] = len(relief_events[relief_events.EVENT_CD == 16])

                game_master[alt + "relief_K"] = len(relief_events[relief_events.EVENT_CD == 3])

                relief_total_runs = relief_events.EVENT_RUNS_CT.sum()
                    
                relief_total_runs -= inherited_runners_scored
                    
                relief_run_events = relief_events[relief_events.EVENT_RUNS_CT != 0]

                for j in range(len(relief_run_events)):
                    
                    unearned_runs = re.findall(unearned_flag, relief_run_events.iloc[j]['EVENT_TX'])
                    
                    relief_unearned += len(unearned_runs)
                
                relief_total_runs -= relief_unearned

                game_master[alt + "relief_ER"] = relief_total_runs

        return(game_master)

if __name__ == "__main__":

    event_parser = EventParser()

    event_parser.parse_events()




        








