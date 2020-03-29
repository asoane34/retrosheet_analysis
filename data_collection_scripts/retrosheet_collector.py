import glob
import os 

def parse_retrograde(in_files, out_file):
    for file in in_files:
        with open(file, 'r') as f:
            for line in f:
                try:
                    stream = line.split(',')
                    out_file.write(stream[0].split('"')[1] + ','\
                                +stream[3].split('"')[1] + ','\
                                +stream[6].split('"')[1] + ','\
                                +stream[12].split('"')[1] + ','\
                                +stream[16].split('"')[1] + ','\
                                +stream[17] + '\n')
                except Exception:
                    continue

if __name__ == '__main__':
    ALL_FILES = glob.glob('data/retro_gamelogs_txt/*.TXT')
    out_file = open('data/retrograde_gamelog.csv', 'w')
    out_file.write('date,away_team,home_team,game_time,park_id,attendance,\n')
    
    parse_retrograde(ALL_FILES, out_file)
    out_file.close()