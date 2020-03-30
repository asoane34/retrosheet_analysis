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

The models discussed in the modeling section do not use the same feature set and thus I cannot discuss one single feature set here but I can discuss the process. During experimentation, different feature sets were selected using an object I created, FeatureSelector (__please see recursive_selection.py in the /tools/ directory of the main repo__). Using a suite of machine learning algorithms, FeatureSelector evaluates a feature set using K-Fold cross validation and a specified metric (Area Under ROC curve in this case, but it could be any desired metric), removes features that are not contributing to the model (either features with low feature importance for tree based algorithms or features with small coefficients for linear algorithms), and re-evaluates until the feature frame can no longer be reduced. Different algorithms emphasized different features, but the most frequently appearing features are: 

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

# Modeling

## KPI / Evaluation Metrics

Looking from the outside in, it would seem that generating a gambling model based on team wins and team losses is a simple binary classification model. Binary classification has many different metrics to evaluate model performance: Accuracy, precision, F1-score, ROC Area Under the Curve, etc. However, none of these are sufficient in evaluating a gambling model. It is more than possible to achieve a high accuracy (relatively, accuracy in predicting baseball outcomes is never that high) and still produce a betting scheme that loses money. The FiveThirtyEight predictions demonstrate this point perfectly. FiveThirtyEight, as mentioned previously, maintains the MLB Elo model which is an extremely popular and successful baseball model and is considered somewhat of a gold standard in predictive power. For the 2019 baseball season, the FiveThirtyEight model accurately forecasts $59.82\%$ of baseball games. While building my own models that strictly predict game outcome, please see __SGDClassifiers.ipynb__ in the __model_experimentation__ directory, I was able to predict with very similar results, accurately forecasting $59.99\%$ of games. But look at the profit generated by the FiveThirtyEight scheme: 

![EloBase](neural_net/bankroll_images/elo_base.png)

Even though the games were predicted with almost $60\%$ accuracy, the betting scheme still loses money on the season. You'll also notice that the results are not a tremendous improvement upon just flipping a coin to decide each game.

![RandomChoice](neural_net/bankroll_images/random_base.png)

The reason being is the aforementioned VIG: Betting favorites, who win more frequently, yields lower payouts. The only metric that matters in evaluating betting schemes is bettor profit, and therefore this will be the only metric considered in evaluating models. 

## Methodology

There are many different ways to frame and approach this problem, and I have tried nearly all of them. The problem can be framed as a Regression problem, a Binary Classification problem, or a Multi-Class classification problem. While I would enjoy discussing all the different methods and their respective shortcomings and strengths, in the interest of time I will only discuss two methods that showed promising results. 

## A Note on Data
The two models outlined below are trained on different feature sets. I will include the features used in each model and the data preparation techniques within each model. However, the commonality of both models is that they were trained on data from past seasons and used to predict the 2019 season. The point is to use past seasons to build a model to predict the next season, so randomly splitting into training and validation sets did not make sense in this case. 

## Deep Learning - Binary Classification with Gaussian Rank Scaler

__Notebook reference: GAUSSRANK_FEEDFORWARD_NN.ipynb__

The technique that showed the most promise was a Fully Connected Feed Forward, Back Propagation Deep Neural Network. This is the only model that was trained on the entire feature set. Each continuous feature was prepared with a technique called GaussRank scaling. The algorithm is as follows: 

* Each unique value in given feature $\alpha_{i}$ is ranked and forced into a distribution between $[-1, 1]$. 
* Sufficiently small $\epsilon$ is chosen and applied to $min(\alpha_{i})$ and $max(\alpha_{i})$ such that the domain endpoints are not inclusive: $(-1, 1)$
* The inverse error function is applied to each value. The Gaussian error function is defined as:
    
    $$erf(x) = \frac{1}{\sqrt\pi}\int_{-x}^{x}e^{-t^{2}}dt$$

    This represents the probability that for a random variable $Z$ with $\mu = 0$ and $\sigma = \frac{1}{2}$,  $erf(x)$ is the probability that $Z$ falls in the range $[-x, x]$. The inverse of this function maps the ranked values to a Gaussian distribution.

I selected a GaussRank scaler for several reasons. Rank transformations are robust to outliers and there were large outliers in the dataset, particulary in the beginning of seasons. However, they were not removed because the observations were accurate. There also was huge differences in variance of features, and thus normalization is beneficial. 

One drawback of the GaussRank scaler: the implementation of the GaussRankScaler that I used <https://github.com/aldente0630/gauss_rank_scaler> does not extrapolate. Intuitively, this makes sense as a value outside the feature's distribution would be outside of the ranked values. Thus, when the transformer object was fit to the training dataset and used to transform the test dataset, a handful of observations were dropped. I am writing an implementation of the GaussRankScaler that addresses this problem, but as of the time of this writing that is not complete. 

The model was trained using Keras, a high level Python API to train Neural Networks on top of the powerful Tensorflow library. 

![nn_arc1](neural_net/gaussrankplot.png)

The architecture for the model, seen above was as follows:

* Densely Connected Input Layer - ReLU activations
* Batch Normalization Layer - Scale activations to Mean $0$ and Standard Deviation $1$.
* Dropout Layer - Reset fraction of activations to $0$.
* Dense Hidden Layer - ReLU activations
* Batch Normalization Layer
* Dropout Layer
* Dense Hidden Layer- ReLu activations
* Batch Normalization Layer
* Dropout Layer
* Dense Output Layer- Sigmoid activation

Each densely connected hidden layer contained $250$ neurons. A Dropout layer fraction of $0.50$ was used in each dropout layer to avoid overfitting. Weights were initialized using the Glorot Normal Distribution: 

$$Weight_{i} \in \bigg[-\frac{\sqrt{6}}{Units_{input} + Units_{output}}, \frac{\sqrt{6}}{Units_{input} + Units_{output}}\bigg]$$

The model was compiled and trained with the following hyperparameters:

* Objective function: Binary crossentropy (log loss): 

    $$L\bigg(y,\hat{y}\bigg) = \frac{1}{m}\displaystyle\sum_{i=1}^{m}-y^{(i)}log(\hat{p}^{(i)})-(1-y^{(i)})log(1-\hat{p}^{(i)})$$
* Optimizer: Adam - a stochastic optimizer, please see <https://arxiv.org/abs/1412.6980v8> for a detailed explanation.
* beta_1 = $0.9$ (optimizer param)
* beta_2 = $0.999$ (optimizer param)
* Learning rate: $0.001$ (optimizer param)
* Batch size: $512$
* Epochs: $25$

The resulting scheme was a vast improvement over the FiveThirtyEight model:

![GaussRankFullPlot](neural_net/bankroll_images/gauss_rank_FF.png)

I evaluated the model on the entire season as that was how I evaluated the FiveThirtyEight model, but if we take the model predictions and attempt an arbitrage strategy, there are other promising results. 

![GaussRankHomeDogs](neural_net/bankroll_images/GR_home_dogs.png)

By betting on only home underdogs, the model is able to generate $44.8\%$ of the profit with only $5\%$ of the plays.

Keep in mind, a betting line is nothing more than an implied win probability. A betting line of $-150$ can be represented as follows: 

$$\frac{1}{1+\frac{100}{150}} = 0.6$$

Thus, by applying this transformation to the probabilities returned by the model, I am able to compare the lines the model generates to the actual lines and determine discrepancies.

If I create a simple arbitrage strategy: 

1. If the model predicted home payout is lower than the actual home payout (the model thinks the home team should be a larger favorite), bet the home team.

2. If the model predicted home payout is higher than the actual home payout (the model thinks the home team should be a larger underdog), bet the road team

the results are better still:

![GaussRankArbitrage](neural_net/bankroll_images/arbitrage.png)

## Deep Learning - Binary Classification with Custom Loss Function

Standard loss functions used in Binary Classification, such as binary cross entropy used above, are not optimized for the task at hand. One way to work around this is to write a loss function that teaches a model how to identify good bets versus bad bets instead of wins versus losses. This loss function looks like this: 

$$L\bigg(y, \hat{y}\bigg) = \displaystyle\sum_{i}^{n}\bigg(P_{1}^{(i)}*y-1\bigg)*ReLU\bigg(P_{1}^{(i)}*\hat{y} -1\bigg) + \bigg(P_{2}^{(i)}*(y-1)-1\bigg)*ReLU\bigg(P_{2}^{(i)}*(1 - \hat{y})-1\bigg)$$

where 

* $P_{1}^{(i)}, P_{2}^{(i)}$ are the payouts of a correct bet placed on the home team and road team respectively. 
* $ReLU = \begin{cases} x & 0 \leq x \lt \infty \\ 0 &  x \lt 0 \end{cases}$

The $ReLU$ function (Rectified Linear Unit) simulates a betting strategy as it only "places" a bet when the value is greater than $0$ and whereas other loss functions punish inaccurate outcome prediction, this loss function punishes bets with no value. An example to illustrate this: Placing a 100 dollar bet on a $-340$ betting favorite has a potential payout of $29$ dollars if the betting favorite wins, while the potential is still $100$. There is limited value to winning such a bet with the same amount of risk as betting on a $+140$ underdog, which would payout $140$ dollars. Now, obviously, the $-340$ favorite will win more often than the $+140$ underdog, but this loss function searches for the bets with value.  

The feature set used in this model was a fraction of full feature set:
* Home Team and Road Team wRC+
* Home Team and Road Team Bullpen wRC+ against
* Home Starter and Road Starter career wRC+ against
* Home and Road Starter season ERA (Earned Run Average of Starting Pitcher, season)
* Home record at home (Number of games above or below .500, 0-based)
* Average Margin of Victory or Loss for Home Team and Road Team
* Home opening moneyline (Betting moneyline for home team)
* Road team record on road (number of games above or below .500, 0-based)
* Current Streak for Home team and Road Team (Either record in last ten games, number of games above or below .500, or if they have won more than ten games in a row, number of consecutive wins) 

The features were scaled to $\mu = 0$ and $\sigma = 1$.

The model was trained also trained using Keras. Keras has functionality for designing and implementing a custom loss function, which was critical for this model design. 

![ModelArc2](neural_net/custom_loss.png)

* Dense Input Layer - ReLU activations
* Batch Normalization Layer - Scale activations to Mean $0$ and Standard Deviation $1$.
* Dense Hidden Layer - ReLU activations
* Dense Hidden Layer- ReLu activations
* Dense Output Layer- Sigmoid activation

Each densely connected hidden layer contained 50 neurons. I experimented with many different configurations of model architecture and experimented with the use of Dropout layers to avoid overfitting and Batch Normalization layers, but this model produced the strongest results.

The model was compiled and trained with:
* Objective function: Custom (outlined above)
* Optimizer: Adam
* beta_1 = $0.9$
* beta_2 = $0.99$
* Learning rate: $0.001$
* Batch size: $32$
* Epochs: $100$

The resulting scheme produced a vast improvement over the SGDClassifier and FiveThirtyEight predictions. 

![NNResults](neural_net/bankroll_images/deep_learning.png)

Due to nature of the loss function (the ReLu function), the probabilities returned by the model were all either very close to $1$ or $0$. Thus, generating an arbitrage strategy as above was not possible. However, there was some additional success if only underdogs were played:

![NNResults2](neural_net/bankroll_images/only_dogs.png)

There is a third model in the main repo directory, an XGBoost model, that has shown flashes of success but I have not been able to recreate my success. I am still tinkering with this model and hope to get that working soon. 

## Conclusion

The Neural Network trained on the entire feature set with the GaussRank scaled data is the only model that showed real promise. Using the scheme of betting on only home underdogs predicted that the model predicted to win, the model would have yielded a ROI (return on investment) of $12.67\%$. Using the model with the arbitrage strategy outlined, the model would have yielded a $5.43\%$ ROI. Given enough volume, these are significant results. However, for the casual sports bettor, I do not recommend quitting your day job. Vegas is not easy to beat, but this has at least shown that there are cracks that can be found.

There are several things I intend to do to further this investigation: 

1. Dimensionality reduction without information loss. Collinearity and multicollinearity are still a problem, even with reduced feature sets. I am working on developing a team rating system, similar to Offensive rating and Defensive rating in the NBA, to incorporate more of the statistics in one feature.

2. Retraining the model throughout the season. Baseball seasons are not directly comparable; I have taken steps to use metrics that compare seasons equally, but they are not perfect. 

3. Looking deeper into the aribtrage strategy using the model predictions. 

4. As does Vegas, every model I built over-weighted home teams. I've tried a host of things to try to correct this: 
    
    * Heavily weighting the ROAD WIN class (even though the classes are not imbalanced) to try to predict more road wins.
    * Heavily weighting underdogs
    * Using multi-label binary classification to try to establish confidence intervals. 

    As of yet, none of these things have worked. But this is the direction I am currently looking farther into. 