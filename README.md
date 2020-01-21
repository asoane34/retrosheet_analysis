# Retrosheet Analysis
This repository contains python scripts that were designed to parse Retrosheet play-by-play files in to game level statistics
for teams and starting pitchers from 1918 (the first year data is available) to 2019. The data was downloaded 
from Retrosheet.org as .EVN files and then parsed using Chadwick (an open source software available via HomeBrew) and 
written to year-level .csv files. The contents are the following:

## event_parser.py
Script parsing yearly .csv files and writing two new .csv files: one containing game level team totals, and the other
containing game level totals for starting pitchers. Transformed over 13 million individual event observations into 
roughly 170000 game observations.

## recursive_selection.py
Creates FeatureSelector object, an object that serves as a jumping-off point in feature selection. Given a feature matrix
(pandas DataFrame) and a target array, FeatureSelector performs recursive feature selection using feature importance,
colinearity, or a combination of both, or random selection. 
