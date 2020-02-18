import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt

class BankrollCalculator():
    def __init__(self, predict_proba, labels, label_dates, home_closing, road_closing, unit = 100.0, with_juice = False, 
                 style = 'all', upper_tol = 0.6, lower_tol = 0.4):
        self.predict_proba = predict_proba
        self.labels = labels
        self.label_dates = label_dates
        self.home_closing = home_closing
        self.road_closing = road_closing
        self.unit = unit
        self.with_juice = with_juice
        self.style = style
        self.upper_tol = upper_tol
        self.lower_tol = lower_tol
        self.plays = None
        self.outcomes = []
        self.play_indices = None
        self.home_reduced = None
        self.road_reduced = None
        self.labels_reduced = None
    
    def plot_profit(self):
        if self.style == 'all':
            self.play_all()
            results_series = pd.Series(self.outcomes)
            result_tracking = pd.concat([self.label_dates, results_series], axis = 1)
            result_tracking.columns = ['date', 'outcome']
            result_tracking['date'] = pd.to_datetime(result_tracking['date'], format = '%Y-%m-%d')
            result_tracking = result_tracking.set_index('date')
            daily_ = result_tracking.resample('D').sum()
            daily_['tracker'] = daily_.outcome.cumsum()
        else:
            self.play_some()
            results_series = pd.Series(self.outcomes)
            play_dates = self.label_dates.iloc[self.play_indices].reset_index(drop = True)
            result_tracking = pd.concat([play_dates, results_series], axis = 1)
            result_tracking.columns = ['date', 'outcome']
            result_tracking['date'] = pd.to_datetime(result_tracking['date'], format = '%Y-%m-%d')
            result_tracking = result_tracking.set_index('date')
            daily_ = result_tracking.resample('D').sum()
            daily_['tracker'] = daily_.outcome.cumsum()
        #plot baseline betting 
        fig, ax = plt.subplots(figsize = (8,8))
        ax.plot(daily_.index, daily_.tracker)
        ax.set_xlabel('Date')
        ax.set_ylabel('Total Profit (Unit of $100/bet)')
        ax.set_title('Total Profit (Betting $100 on each game)');
        
        
    def play_all(self):
        self.get_binary()
        for k in range(len(self.plays)):
            if self.plays[k] and self.labels[k]:
                if self.home_closing.iloc[k] > 0:
                    self.outcomes.append((self.home_closing.iloc[k] / 100.) * self.unit)
                else:
                    if self.with_juice:
                        self.outcomes.append(self.unit)
                    else:
                        self.outcomes.append((100. / (-1 * self.home_closing.iloc[k])) * self.unit)
            
            elif self.plays[k] and not self.labels[k]:
                if self.with_juice and self.home_closing.iloc[k] < 0:
                    self.outcomes.append((self.home_closing.iloc[k] / 100.) * self.unit)
                else:
                    self.outcomes.append(-self.unit)
            
            elif not self.plays[k] and not self.labels[k]:
                if self.road_closing.iloc[k] > 0:
                    self.outcomes.append((self.road_closing.iloc[k] / 100.) * self.unit)
                else:
                    if self.with_juice:
                        self.outcomes.append(self.unit)
                    else:
                        self.outcomes.append((100. / (-1 * self.road_closing.iloc[k])) * self.unit)
            else:
                if self.with_juice and self.road_closing.iloc[k] < 0:
                    self.outcomes.append((self.road_closing.iloc[k] / 100.) * self.unit)
                else:
                    self.outcomes.append(-self.unit)
    
    def play_some(self):
        self.get_plays()
        for k in range(len(self.plays)):
            if self.plays[k] and self.labels_reduced.iloc[k]:
                if self.home_reduced.iloc[k] > 0:
                    self.outcomes.append((self.home_reduced.iloc[k] / 100.) * self.unit)
                else:
                    if self.with_juice:
                        self.outcomes.append(self.unit)
                    else:
                        self.outcomes.append((100. / (-1 * self.home_reduced.iloc[k])) * self.unit)
            
            elif self.plays[k] and not self.labels_reduced.iloc[k]:
                if self.with_juice and self.home_reduced.iloc[k] < 0:
                    self.outcomes.append((self.home_reduced.iloc[k] / 100.) * self.unit)
                else:
                    self.outcomes.append(-self.unit)
            
            elif not self.plays[k] and not self.labels_reduced.iloc[k]:
                if self.road_reduced.iloc[k] > 0:
                    self.outcomes.append((self.road_reduced.iloc[k] / 100.) * self.unit)
                else:
                    if self.with_juice:
                        self.outcomes.append(self.unit)
                    else:
                        self.outcomes.append((100. / (-1 * self.road_reduced.iloc[k])) * self.unit)
            else:
                if self.with_juice and self.road_reduced.iloc[k] < 0:
                    self.outcomes.append((self.road_reduced.iloc[k] / 100.) * self.unit)
                else:
                    self.outcomes.append(-self.unit)
        print('REMINDER! You selected the .play_some method... Extract play indices with .play_indices attr')
        

    def get_binary(self):
        self.plays = [1 if i > 0.5 else 0 for i in self.predict_proba]
    
    def get_plays(self):
        _proba = pd.Series(self.predict_proba)
        self.play_indices = list(_proba[(_proba > self.upper_tol) |
                                              (_proba < self.lower_tol)].index)
        
        self.plays = [1 if i > 0.5 else 0 for i in _proba.iloc[self.play_indices]]
        self.home_reduced = self.home_closing.iloc[self.play_indices].reset_index(drop = True)
        self.road_reduced = self.road_closing.iloc[self.play_indices].reset_index(drop = True)
        self.labels_reduced = pd.Series(self.labels).iloc[self.play_indices].reset_index(drop = True)