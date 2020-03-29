# BETTING BASEBALL 
## Capstone Final Report
### Atticus Soane 

# Can You Beat Vegas From Your Laptop? 

![headerimage](adv_metrics/download.jpg)

There's an old adage in gambling: The House always wins. And while I'm sure your grandmother really does have a slot machine strategy that could bankrupt any casino, this isn't changing anytime soon. They make the rules and they make them so that they will always win. But with the legalization of sports gambling in the United States (at the Federal level at least) and the LEGAL emergence of sports gambling as a multi-billion dollar industry, can an average person leverage machine learning to gain an edge on Vegas oddsmakers? I, an average person, chose to investigate. For the purpose of this investigation, I focused on Major League Baseball - a notoriously difficult league to bet successfully. There were two major guidelines for this investigation.

1. Does the model yield profit? As will be discussed later, it is possible to predict outcomes accurately and still lose money. Any useful model must generate __PROFIT__.

2. Can the model be built with data that is publicly accessible? There is information that can be purchased that would be considered "Inside Vegas" information: ticket counts, money percentages, etc. That is outside the scope of this investigation. I will only use data that is public domain. 

Now before we dive in, a quick sports gambling primer for those unacquainted with the sports gambling space. There are far too many different types of bets for me to try to explain here: if you want to go find some value in __Compact Win or Tie Only__ bets more power to you. This project will focus on two of the three most common baseball bets: Betting the __Moneyline__ and betting the __Runline__. 

*  __Moneyline__:

    This is the most basic of all sports bets: the bettor is simply betting on which team will win the game. The score is of no consequence as long as the bettor correctly picks the winning team. The payout of this bet is simply determined by the line offered for the winning team. Typically, the lines displayed are called American style: they indicate the return on a $100$ dollar wager. A negative line value indicates the betting favorite: the team expected to win. The return on such a bet would be calculated as follows:  
            
            
    $$\displaystyle\frac{100}{-1 * line_{fav}}*BettingUnit$$

    For example, if the line offered for the winning team was $-150$, the payout for a $100$ dollar bet would be calculated as follows: 

    $$\displaystyle\frac{100}{-1*-150}*100=66.67$$

    As you can see, this is not a 1 to 1 payout. The difference between the actual payout and what a 1 to 1 payout would be is called the __VIG__ and is often colloquially referred to as "juice". We will discuss this in much more detail later. 

    Now, if the line value is greater than zero, this indicates the betting underdog. This is a much simpler calculation: 

    $\displaystyle\ \frac{line_{underdog}}{100}*BettingUnit$

    So, if the line was $+150$, the payout for a $100$ dollar wager would be:

    $$\displaystyle\frac{150}{100}*100=150$$ 

* __Runline__:

    This is an adaptation of what is referred to as "spread betting" in basketball and football betting. In spread betting, the bettor has to accurately predict whether the score differential between two teams will fall in a certain range. In typical spread betting, the spread varies from matchup to matchup. Runline betting does not work exactly like this. While the concept is the same, forecasting a score differential, that value is typically set at $1.5$ for all games, and the only thing that changes is the payout. Let's go through a quick example to illustrate this. For example: team A is a $-119$ MONEYLINE favorite over underdog team B ($+109$ Moneyline). In this case, the RUNLINE will be set at $-1.5$ for team A with a $+170$ payout and $+1.5$ for team B with a $-200$ payout. The payouts mentioned are calculated the same way as shown for the Moneyline payouts above. Now, there are three possible scenarios here:

    * Team A wins by more than $1.5$. This would be considered the favorite "covering" the runline. A bet placed on team A to cover the Runline would payout at $+170$, so $1.7$ times the wagered amount.
    * Team A wins, but by less than $1.5$. This would be considered the underdog team B covering the runline. A bet placed on team B to cover the Runline would payout at $-200$, so $0.5$ times the wagered amount. 
    * Team B wins. In this case, team B wins and covers and the a bet placed on team B to cover the runline would payout at $-200$.

    # DATA COLLECTION

    There is a virtually limitless amount of baseball data available going back to the founding of the league in the 1800s. In order to give myself the greatest opportunity to find an edge, I collected data from the following sources: 

    1. __NOAA Global Historical Climatology Network__-
    <ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/daily/> 
    
         Using the GHCN FTP, I collected daily weather observations for a myriad of weather stations throughout the United States and created a database of weather obervations for each baseball game dating back to the 1900s. Please see: __noaa_weather_collection.py__ and  __expanded_stations.py__ in the __data_collection_scripts__ directory  and __data_prep/data_collection_preparation.ipynb__.

    2. __Retrosheet__- 
    <https://www.retrosheet.org/game.htm>, <https://www.retrosheet.org/gamelogs/index.html>

        The vast majority of the baseball data collected was collected from the vast Retrosheet database. This is all open source and Retrosheet provides two major data downloads: Retrosheet gamelogs, which contain basic high level game information such as location, game time, the teams involved, and attendance, and then the Retrosheet play-by-play files, which contain a record of every event that occured in every MLB game dating back to 1918 (Seriously, every single play. Groundout, popout, single, balk, walk, you name it, it's in there). This is a huge dataset of over 13 million observations. There is an open source software called Chadwick which can be used to download the .EVN files available via the Retrosheet data dump and parse these files into .CSV files on your local machine. From there, I wrote a program to extract key baseball statistics from these event files. The statistics I chose were based on both extensive personal knowlege of the sport of baseball (I played in college) and research, and I will discuss them more later. The great challenge here is that I needed every teams' statistics and every pitcher's statistics on each given day of the season, so I had to iterate through the dataframe and recreate each teams' statistics on each day of the season. Please see: __event_parser.py__, __team_stat_generator.py__, __pool_executor_pitching.py__, __starting_pitchers.py__, __double_header.py__, and __retrosheet_collector.py__ in the __data_collection_scripts__ directory, and __data_prep/retrosheet_gamelogs.ipynb__. 

    3. __FiveThirtyEight__- 
    <https://github.com/fivethirtyeight/data/tree/master/mlb-elo>

        FiveThirtyEight maintains an Elo dataset which contains a number of team and pitcher ratings generated using the Elo rating system. The Elo rating system is a technique popularized by chess for ranking relative skill in zero-sum games. You can read more about the contents of the FiveThirtyEight Elo system here <https://fivethirtyeight.com/features/how-our-mlb-predictions-work/>. Thankfully, this dataset is available to download as a .CSV from the link above. 

    4. __Baseball-Reference__-  <https://www.baseball-reference.com/>
        Baseball-Reference is another treasure trove of information. I collected stadium names and locations for each season since 1903, as well as stadium information such as a rating system for whether each stadium favors the pitcher or the hitter. Please see: __scraper_team_stadium.py__ in the __data_collection_scripts__ directory. 

    5. __SportsBookReview__ <https://sportsbookreviewsonline.com/scoresoddsarchives/mlb/mlboddsarchives.htm> 

        This data was not included in initial models (because I was not able to find historical gambling odds going back past 2010 and I was using a dataset from 1918 to 2019), but when initial attempts using only baseball statistics failed to yield promising results, I collected historical betting odds to use as a feature as these are publicly accessible. Please see: __02betting_lines_application.ipynb__ in the __model_experimentation__ directory.

    6. __FanGraphs__ <https://www.fangraphs.com/guts.aspx?type=cn>

        FanGraphs maintains extensive statistics and records. Many of the statistics used have multipliers / constants unique to the year. I scraped these from FanGraphs. Please see: __advanced_metric_collection.ipynb__ in the __data_collection_scripts__ directory. 


# DATA PREPROCESSING

There was a great deal of preparation necessary to aggregate all of the data sources into a single dataset. The primary challenge was creating a common key to merge all of the different datasets into a master dataset. This was extremely time consuming but adds absolutely nothing to the understanding of the project so I will not discuss it here.  If you'd like to see how the dataset was assembled, please help yourself to the notebooks in the __data_prep/__ directory, particulary the __data_collection_preparation.ipynb__ notebook, and the Python scripts listed in the Data Collection section above. 

# FEATURE SET / FEATURE ENGINEERING / FEATURE IMPORTANCE

## TARGET FEATURE

As with any machine learning problem, the first question to answer is what are we trying to predict? There are many different ways to frame this problem, I elected to create a target feature HOME WIN - a simple binary feature with level $1$, the home team won, or $0$, the home team lost. The reason I chose HOME WIN as opposed to shuffling the data randomly and assigning a binary target feature was two-fold. During data exploration I noticed two interesting patterns: 

![HomeFavDist](adv_metrics/adv_metric_plots/home_favorite_distribution.png)

![HomeFavDist](adv_metrics/adv_metric_plots/home_win_distribution.png)

The home team is set as the betting favorite over $70\%$ games, but home team only wins $53\%$ of these games. That means that road underdogs are winning $47\%$ of their games, which is actually a higher percentage than home underdogs; home underdogs only win games at a little over a $43\%$ clip:

![HomeDogsDist](adv_metrics/adv_metric_plots/home_dogs_distribution.png)

This is both counter-intuitive and presents an area to potentially exploit. If we can find the discrepancy in home team favorites and home team wins, we can generate profit in that window. 

## FEATURE SET

The feature set I considered is too large to list here, but the features fall in to several categories:

* TEAM BASED STATISTICS - Team offensive and relief pitching statistics. 

    * The offensive statistics I chose to analyze were: OPS, wOBA, wRAA, wRC, runs per game and hits per game. The relief pitching statistics I chose to anlayzer were: K/9, K/BB, WHIP, ERA, FIP, wOBA against, wRAA against, and WRC against. It would be another paper entirely to explain all of these but please see <https://library.fangraphs.com/offense/> for detailed explanation of the calculation and meaning of these statistics.

* STARTING PITCHER STATISTICS - Statistics for the starting pitcher of each team.

    * Statistics considered were K/9, K/BB, WHIP, ERA, FIP, wOBA against, wRAA against, and wRC against. Please see <https://library.fangraphs.com/pitching/> for reference. 

* FIVETHIRTYEIGHT RATINGS - Ratings used in FiveThirtyEight modeling. Please see: <https://fivethirtyeight.com/features/how-our-mlb-predictions-work/>, a detailed explanation of the FiveThirtyEight modeling technique.

* GAMBLING STATISTICS - Consensus betting lines that incorporate line movement. Monitoring the change between the opening betting line and the closing betting line can give a rough estimate of how bettors predicted the game.

* EXTERNAL FEATURES - Attendance, weather, distance traveled, factors accounting for different ballparks, etc. These are values independent of the teams on the field. 

* MOMENTUM - While it is impossible to quantify momentum, I tried to. These features reflect a team's recent performance and trends.

## FEATURE ENGINEERING

As briefly mentioned in the Data Collection section, all team and pitcher statistics had to be created. While there are many records of season-end and game-end statistics, for the purpose of predictive modeling I needed each teams' statistics and each pitchers' statistics on every day of the season, as well as season trends for each team. These were created using the scripts in the __data_collection_scripts.py__ directory.  

## FEATURE SELECTION

The models discussed in the modeling section do not all use the same feature set and thus I cannot discuss one single feature set here but I can discuss the process. Feature sets were selected using an object I created, FeatureSelector (__please see recursive_selection.py in the /tools/ directory of the main repo__). Using a suite of machine learning algorithms, FeatureSelector evaluates a feature set using K-Fold cross validation and a specified metric (Area Under ROC curve in this case, but it could be any desired metric), removes features that are not contributing to the model (either features with low feature importance for tree based algorithms or features with small coefficients for linear algorithms), and re-evaluates until the feature frame can no longer be reduced. Different algorithms emphasized different features, but the most frequently appearing features are: 

![FeatureImportance](adv_metrics/adv_metric_plots/feature_importance.png)

A major issue during this process was collinearity and multicollinearity.

 Many of the team and pitcher statistics are highly correlated, but removing them resulted in information loss, as the features most important to the model were also the highly collinear and multicollinear features. Multicollinearity was calculated using the Variance Inflation Factor: 

 $$VIF_{\hat\alpha_{i}} = \displaystyle\frac{1}{1 - R_{i}^{2}}$$ 

 where $R_{i}^{2}$ is the coeffiecient of determination for each feature $\alpha_{i}$ with respect to all other features - the proportion of variance in each feature that can be explained by all other features. A thorough explanation can of VIF can be found here: <https://en.wikipedia.org/wiki/Variance_inflation_factor>

 ![Collinearity](adv_metrics/adv_metric_plots/correlation.png)

 ![Multicollinearity](adv_metrics/adv_metric_plots/VIF.png)
 
 To overcome this, the final models are primarily centered one one statistics: wRC+. wRC+ is a $100$-based statistic and thus it allows for relative comparison on a single scale as relative comparison between eras. Using the $2019$ season, it can be seen that statistic is an effective rating tool of performance that provides a smooth distribution: 

![2019wRCDist](adv_metrics/adv_metric_plots/2019wRC+.png)


![2019wRCBullpenDist](adv_metrics/adv_metric_plots/2019BullpenwRC+.png)