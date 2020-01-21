import glob
import pandas as pd 

starter_frames = []
starter_files = glob.glob('./aggregated_event_files/starter_stats_*.csv')
for file in starter_files:
    df = pd.read_csv(file)
    df['date'] = pd.to_datetime(df['date'], format = '%Y-%m-%d')
    df['year'] = pd.DatetimeIndex(df.date).year
    df = df.sort_values(by = ['date']).reset_index(drop = True)
    
    df = df.assign(is_doubleheader = 0, is_tripleheader = 0)
    game_counts = df.groupby('team_code').date.value_counts()

    double_headers = game_counts[game_counts == 2]
    triple_headers = game_counts[game_counts > 2]

    all_double_headers = []
    for j in double_headers.index:
        all_double_headers.append(j)

    all_triple_headers = []
    for k in triple_headers.index:
        all_triple_headers.append(k)

    for index in all_double_headers:
        game_indices = df[(df.team_code == index[0]) & (df.date == index[1])].index
        if len(game_indices) > 1:
            df.at[game_indices[1], 'is_doubleheader'] = 1
        else:
            print(index)

    for index_ in all_triple_headers:
        game_indices_ = df[(df.team_code == index_[0]) & (df.date == index_[1])].index
        if len(game_indices_) == 3:
            df.at[game_indices_[1], 'is_doubleheader'] = 1
            df.at[game_indices_[2], 'is_tripleheader'] = 1
        else:
            print(index_)
    starter_frames.append(df)
    