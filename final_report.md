# BETTING BASEBALL 
## Capstone Final Report
### Atticus Soane 

# Can You Beat Vegas From Your Laptop? 

There's an old adage in gambling: The House always wins. And while I'm sure your grandmother really does have a slot machine strategy that could bankrupt any casino, this isn't changing anytime soon. They make the rules and they make them so that they will always win. But with the legalization of sports gambling in the United States (at the Federal level at least) and the LEGAL emergence of sports gambling as a multi-billion dollar industry, can an average person leverage machine learning to gain an edge on Vegas oddsmakers? I, an average person, chose to investigate. There are certainly professional gamblers, colloquially referred to as "sharps", who bet thousands and thousands of dollars a game and make their living in Vegas sportsbooks. If you take a quick scroll through Twitter, you can also find plenty of blow-hards who label themselves professional gamblers but in reality have the same success rate as a standard two-sided coin. The scope of this investigation falls somewhere in between these two extremes: Is it possible to build a predictive model using data that is readily accessible to the public to gain an edge on bookmakers? The key focus here is on the "readily accessible" data. It is possible to pay services to provide what would be considered "inside Vegas" information such as what percentage of the money is on each team, what percentage of the total bets are on each team, etc. But my focus will be solely on building models using data that anyone can collect from their laptop. To test my hypothesis, I have chosen a sport with a vast treasure trove of available data that is notoriously difficult to bet: Baseball. Anybody who has any experience sports gambling can speak to what a dangerous beast betting on baseball is. Baseball is unique among sports in that the team on the field differs vastly from game to game: a team playing behind its ace pitcher can be virtually unstoppable whereas they turn back into a pumpkin when playing behind the fifth starter in the rotation. They also play more than double the games of any of the other major professional and there is the least variance between the winning percentages of the top teams and the bottom teams.

Now before we dive in, a quick sports gambling primer for those unacquainted with the sports gambling space. There are far too many different types of bets for me to try to explain here: if you want to go find some value in __Compact Win or Tie Only__ bets more power to you. This project will focus the two of the three most common baseball bets: Betting the __Moneyline__ and betting the __Runline__. 

*  __Moneyline__:

    This is the most basic of all sports bets: the bettor is simply betting on which team will win the game. The score is of no consequence as long as the bettor correctly picks the winning team. The payout of this bet is simply determined by the line offered for the winning team. Typically, the lines displayed are called American style: they indicate the return on a $100$ dollar wager. A negative line value indicates the betting favorite: the team expected to win. The return on such a bet would be calculated as follows:  
            
            
    $\displaystyle\frac{100}{-1 * line_{fav}}*BettingUnit$

    For example, if the line offered for the winning team was $-150$, the payout for a $100$ dollar bet would be calculated as follows: 

    $\displaystyle\frac{100}{-1*-150}*100=66.67$

    As you can see, this is not a 1 to 1 payout. The difference between the actual payout and what a 1 to 1 payout would be is called the __VIG__ and is often colloquially referred to as "juice". We will discuss this in much more detail later when we come to discussing optimization of loss functions. 

    Now, if the line value is greater than zero, this indicates the betting underdog. This is a much simpler calculation: 

    $\displaystyle\ \frac{line_{underdog}}{100}*BettingUnit$

    So, if the line was $+150$, the payout for a $100$ dollar wager would be:

    $\displaystyle\frac{150}{100}*100=150$ 

* __Runline__:

    This is an adaptation of what is referred to as "spread betting" in basketball and football betting. In spread betting, the bettor has to accurately predict whether the score differential between two teams will fall in a certain range. In typical spread betting, the spread varies from matchup to matchup. Runline betting does not work exactly like this. While the concept is the same, forecasting a score differential, that value is typically set at $1.5$ for all games, and the only thing that changes is the payout. Let's go through a quick example to illustrate this. For example: team A is a $-119$ MONEYLINE favorite over underdog team B ($+109$ Moneyline). In this case, the RUNLINE will be set at $-1.5$ for team A with a $+170$ payout and $+1.5$ for team B with a $-200$ payout. The payouts mentioned are calculated the same way as shown for the Moneyline payouts above. Now, there are three possible scenarios here:

    * Team A wins by more than $1.5$. This would be considered the favorite "covering" the runline. A bet placed on team A to cover the Runline would payout at $+170$, so $1.7$ times the wagered amount.
    * Team A wins, but by less than $1.5$. This would be considered the underdog team B covering the runline. A bet placed on team B to cover the Runline would payout at $-200$, so $0.5$ times the wagered amount. 
    * Team B wins. In this case, team B wins and covers and the a bet placed on team B to cover the runline would payout at $-200$. 
    
    Now, there is a great deal more to discuss moving forward, but this is enough to get started. 

    # DATA COLLECTION

    There is a virtually unlimited amount of baseball data available going back to the founding of the league in the 1800s. In order to give myself the greatest opportunity to find an edge, I collected data from the following sources: 

    1. __NOAA Global Historical Climatology Network__-
    <ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/daily/> 
    
         Using the GHCN FTP, I collected daily weather observations for a myriad of weather stations throughout the United States and created a database of weather obervations for each baseball game dating back to the 1900s. Please see: __noaa_weather_collection.py__ __expanded_stations.py__,  and __data_prep/data_collection_preparation.ipynb__.

    2. __Retrosheet__- 
    <https://www.retrosheet.org/game.htm>, <https://www.retrosheet.org/gamelogs/index.html>

        The vast majority of the baseball data collected was collected from the vast Retrosheet database. This is all open source and Retrosheet provides two major data downloads: Retrosheet gamelogs, which contain basic high level game information such as location, game time, the teams involved, and attendance, and then the Retrosheet play-by-play files, which contain a record of every event that occured in every MLB game dating back to 1918 (Seriously, every single play. Groundout, popout, single, balk, walk, you name it, it's in there). This is a huge dataset of over 13 million observations. There is an open source software called Chadwick which can be used to download the .EVN files available via the Retrosheet data dump and parse these files into .CSV files on your local machine. From there, I wrote a program to extract key baseball statistics from these event files. The statistics I chose were based on both extensive personal knowlege of the sport of baseball (I played in college) and research, and I will discuss them more later. The great challenge here is that I needed every teams' statistics and every pitcher's statistics on each given day of the season, so I had to iterate through the dataframe and recreate each teams' statistics on each day of the season. Please see: __event_parser.py__, __team_stat_generator.py__, __pool_executor_pitching.py__, __starting_pitchers.py__, __double_header.py__, __retrosheet_collector.py__, and __data_prep/retrosheet_gamelogs.ipynb__. 

    3. __FiveThirtyEight__- 
    <https://github.com/fivethirtyeight/data/tree/master/mlb-elo>

        FiveThirtyEight maintains an Elo dataset which contains a number of team and pitcher ratings generated using the Elo rating system. The Elo rating system is a technique popularized by chess for ranking relative skill in zero-sum games. You can read more about the contents of the FiveThirtyEight Elo system here <https://fivethirtyeight.com/features/how-our-mlb-predictions-work/>. Thankfully, this dataset is available to download as a .CSV from the link above. 

    4. __Baseball-Reference__-  <https://www.baseball-reference.com/>
        Baseball-Reference is another treasure trove of information. I collected stadium names and locations for each season since 1903, as well as stadium information such as a rating system for whether each stadium favors the pitcher or the hitter. Please see: __scraper_team_stadium.py__. 

    5. __SportsBookReview__ <https://sportsbookreviewsonline.com/scoresoddsarchives/mlb/mlboddsarchives.htm> 

        This data was not included in initial models (because I was not able to find historical gambling odds going back past 2010 and I was using a dataset from 1918 to 2019), but when initial attempts using only baseball statistics failed to yield promising results, I collected historical betting odds to use as a feature as these are publicly accessible. Please see: __02betting_lines_application.ipynb__.


# DATA PREPROCESSING

There was a great deal of preparation necessary to aggregate all of the data sources into a single dataset. The primary challenge was creating a common key to merge all of the different datasets into a master dataset. This was extremely time consuming but adds absolutely nothing to the understanding of the end goal so I won't go into it here.  If you'd like to see how the dataset was assembled, please help yourself to the notebooks in the __data_prep/__ directory, particulary the __data_collection_preparation.ipynb__ notebook, and the Python scripts listed in the Data Collection section above. 

# FEATURE SET / FEATURE ENGINEERING / FEATURE IMPORTANCE

The final feature set contained hundreds of features

