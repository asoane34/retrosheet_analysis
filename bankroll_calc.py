from dataclasses import dataclass, field
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt 

@dataclass
class BankrollCalculator():
    predict_proba: np.ndarray
    labels: np.ndarray
    label_dates: pd.Series
    home_odds: np.ndarray
    road_odds: np.ndarray
    unit: int = 100
    with_juice: bool = False
    style: str = "all"
    upper_tol: float = 0.6
    lower_tol: float = 0.4
    plays: list = field(default_factory = list)
    betting_outcomes: list = field(default_factory = list)
    fig_title: str = None
    save_fig: bool = False
    img_dest: str = None

    def plot_profit(self):

        self.play_all()

        total_profit = sum(self.betting_outcomes)

        n_plays = len(self.betting_outcomes)

        results_series = pd.Series(self.betting_outcomes)

        result_tracking = pd.concat([self.label_dates, results_series], axis = 1)

        result_tracking.columns = ["date", "outcome"]

        result_tracking["date"] = pd.to_datetime(result_tracking.date, format = "%Y-%m-%d")

        result_tracking = result_tracking.set_index("date")

        daily_ = result_tracking.resample("D").sum()

        daily_["tracker"] = daily_.outcome.cumsum()

        fig, ax = plt.subplots(figsize = (8,8))

        ax.plot(daily_.index, daily_.tracker)

        ax.axhline(0.0, ls = "--", c = "r", xmin = 0., xmax = 1)

        results_str = "\n".join((
            "Total Profit: {}".format(str(total_profit)), 
            "Total Plays: {}".format(str(n_plays))
        ))

        text_box = {
            
            "boxstyle" : "square",

            "facecolor" : "mistyrose",

            "edgecolor" : "k",

            "alpha" : 0.5
        }

        ax.text(0.01, 0.99, results_str, transform = ax.transAxes, fontsize = 12, verticalalignment = "top",
        bbox = text_box)

        ax.set_xlabel('Date')

        ax.set_ylabel('Total Profit (Unit of ${}/bet)'.format(str(self.unit)))

        ax.set_title(self.fig_title);
        
        if self.save_fig:
            
            plt.savefig(self.img_dest)
            
            print("Graphic written to file {}".format(self.img_dest))
    
    def play_all(self):

        self.get_plays()

        for k in range(len(self.plays)):

            if self.plays[k] == 1 and self.labels[k] == 1:

                if self.home_odds[k] > 0:

                    self.betting_outcomes.append((self.home_odds[k] / 100.) * self.unit)

                else:

                    if self.with_juice:

                        self.betting_outcomes.append(self.unit)

                    else:

                        self.betting_outcomes.append((100. / (-1* self.home_odds[k])) * self.unit )

            elif self.plays[k] == 1 and self.labels[k] != 1:

                if self.with_juice and self.home_odds[k] < 0:

                    self.betting_outcomes.append( (self.home_odds[k] / 100.) * self.unit)

                else:

                    self.betting_outcomes.append( -self.unit)

            elif self.plays[k] == 0 and self.labels[k] == 0:

                if self.road_odds[k] > 0:

                    self.betting_outcomes.append((self.road_odds[k] / 100.) * self.unit)

                else:

                    if self.with_juice:

                        self.betting_outcomes.append(self.unit)

                    else:

                        self.betting_outcomes.append( (100. / (-1 * self.road_odds[k])) * self.unit)

            elif self.plays[k] == 0 and self.labels[k] != 0:

                if self.with_juice and self.road_odds[k] < 0:

                    self.betting_outcomes.append( (self.road_odds[k] / 100.) * self.unit)

                else:

                    self.betting_outcomes.append( -self.unit)

            else:

                self.betting_outcomes.append(0) 


    def get_plays(self):

        try:
            
            if self.predict_proba.shape[1] == 1:

                self.plays = [1 if i > 0.5 else 0 for i in self.predict_proba]

            elif self.predict_proba.shape[1] == 2:

                self.plays = [1 if i[0] > 0.5 else 0 for i in self.predict_proba]

            else:

                for k in self.predict_proba:

                    if k[0] > k[1] and k[0] > k[2]:

                        self.plays.append(1)
                    
                    elif k[1] > k[0] and k[1] > k[2]:

                        self.plays.append(0)

                    else:

                        self.plays.append(2)

        except:

            self.plays = [1 if i > 0.5 else 0 for i in self.predict_proba]



