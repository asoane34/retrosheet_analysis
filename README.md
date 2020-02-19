# retrosheet_analysis
Modeling to predict outcome of MLB baseball games and generate a profitable betting strategy.

# Current Repository Contents

## data_prep/
This directory contains data collection, cleaning, and preparation notebooks. Data for this project was collected from FiveThirtyEight, Retrosheet.org, baseball-reference.com, sportsbookreview.com, the United States Geological Survey, and the NOAA Global Historical Climatology Network. 

## 00EDA-FeatureEngineering.ipynb
Jupyter Notebook exploring and cleaning primary dataframe, as well as creating momentum based features. 

## 01classification_win_loss
Jupyter Notebook performing binary classification on home team win or loss. Emphasis here is on Feature Selection and determining best feature subsets to perform further modeling. 

## 01regression_attempt.ipynb
(Largely unsuccessful) attempt at predicting score differential in each game. __Will revisit once classification model is optimized (win/loss classification as a potential feature)__

## 02betting_lines_application.ipynb
Initial attempts were to gain an edge using only team based performance statistics, collected and incorporated Vegas gambling odds as potential feature. 

## 03betting_lines_application.ipynb
Exploration of deep learning models, proof of concept for custom objective function and dimensionality reduction

## 04final_application.ipynb
Current modeling steps: application as times series, deep learning / gradient boosting machines (with custom -Vegas- weights) 

## bankroll_calculator.py
Python script defining custom evaluation metric. As the purpose of the model is to generate a profitable betting strategy, the evaluation metric must reflect gambling profits. 

## double_header.py
Python script addressing the double header issue: non unique merge keys between dataframes. 

## event_parser.py
Python script parsing 13 million play-by-play observations from Retrosheet.org in to 197000 usable game level observations with team statistics

## expanded_stations.py
Extension of weather collection from NOAA global historical climatology network

## feature_creator.py
Python script creating TeamFeatureEngineer, an attempt to capture momentum-based statistics. Generated season by season trends such as home run differential, road run differential, current winning streaks, etc. 

## noaa_weather_collection.py
Python script collecting weather daily weather observations for the past 100 years from NOAA global historical climatology network

## pool_executor_pitching.py
Python script creating database of all starting pitchers from 1918 until the present season and aggregating observations into single dataframe. 

## recursive_selection.py
Python script creating FeatureSelector object. Allows user to perform advanced analysis of feature subsets, evaluate subsets and select best feature set for a machine learning problem. 

## scraper_team_stadium.py
Python script scraping team stadium information from baseball-reference.com

## retrosheet_collector.py
Python script collecting all Retrosheet season files created by event_parser script 

## starting_pitchers.py
Python script collecting all starting pitcher data
