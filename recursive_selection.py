
''' 
FeatureSelector is an object that hopefully serves as a jumping-off point in Feature Selection. 
Given a feature DataFrame and a target array, 
FeatureSelector performs recursive or random feature selection using feature importance, 
colinearity, or a combination of the two. At the moment,
it only works with ML algorithms with an sklearn API wrapper, but that will change as I add more methods for 
selecting features. Obviously, to use feature importance as a method in feature selection, 
the algorithm must have a .feature_importances_ attribute or a coef_, but if 'corr'
or 'random' are specified as the method, then any algorithm with an Sklearn API can be used.
It works with Classifiers or Regressors, the only notable difference would be the
need to change the 'metric' parameter to 'rmse'.
The default algorithm is the RandomForestClassifier with default hyperparameters, but 
hyperparameters can be specified in a dictionary passed to the
'params' parameter.
'''

from concurrent.futures import ProcessPoolExecutor #Multiprocessing used in training on all train/test splits at once
from dataclasses import dataclass, field
import sys
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler #scale data
from sklearn.model_selection import KFold #generate train/test split indices
from sklearn.ensemble import RandomForestClassifier #default algorithm, can pass other algorithms as long as they have sklearn wrapper
from sklearn.metrics import accuracy_score, precision_score, f1_score, mean_squared_error, roc_auc_score #possible scoring metrics
from statsmodels.stats.outliers_influence import variance_inflation_factor

@dataclass
class FeatureSelector():
    X: pd.core.frame.DataFrame
    y: pd.core.frame.Series
    algorithm: object = RandomForestClassifier()
    scale: str = None
    method: str = "importance"
    metric: str = "acc"
    drop_corr: bool = False
    VIF: bool = False
    VIF_tol: float = 10.
    early_stopping: bool = False
    stopping_thresh: int = 3
    params: dict = field(default_factory = dict) 
    cv: int = 5
    sample_size: float = 0.5
    drop_size: int = 1
    correlation_tolerance: float = 0.9
    corr_lower_by: float = 0.1
    correlation_strategy: str = "tol"
    n_iterations: int = 20
    n_jobs: int = None
    verbose: int = 0
    X_reduced: pd.core.frame.DataFrame = None
    current_eval: float = 0.
    best_eval: float = 0. 
    feature_importances: np.ndarray = None
    current_subset: list = field(default_factory = list)
    best_subset: list = field(default_factory = list)
    importance_frame: pd.core.frame.DataFrame = None
    performance_log: dict = field(default_factory = dict)

    ''' 
    Initialize FeatureSelector object
        Args:
            X [pd.DataFrame]: Feature matrix 
            y [array]: Target variable, (pandas series or np.array)
            algorithm [func]: Algorithm used in determining feature importances and evaluating metric: MUST BE COMPATIBLE WITH SKLEARN API,
                i.e. .feature_importances_ or coef_ attribute
            scale [str] : Method of feature scaling to employ. Acceptable values:
                None - No scaling
                'standard' - sklearn StandardScaler (features scaled to mean 0 variance 1)
                'minmax' - sklearn MinMaxScaler (features scaled to min 0 max 1)
            method [str]: Method of feature selection to pursue, acceptable values:
                'importance' : Select recursively using feature importance
                'corr' : Select recursively using feature correlation
                'both' : Use combination of feature importance and feature correlation
                'random' : Must be used with random_cv method, indicates random selection of features not recursive
            metric [str]: Metric to be used for evaluation. Acceptable values:
                'acc' : accuracy score (default)
                'precision' : precision
                'f1' : f1 score
                'rmse' : root mean squared error
            drop_corr [bool] : Boolean flag to drop correlated features above a certain tolerance before performing recursive feature 
                selection. Can be used with either recursive or random selection. This is an alternative to recursively removing 
                correlated features using method: 'corr', so keep flag as False if using method 'corr'.
            VIF [bool] : boolean flag to recursively remove features with VIF over a given tolerance
            VIF_tol [int/float] : Int/float with maximum level of tolerance for VIF
            early_stopping [bool]: Boolean flag to stop after specified rounds with improvement
            stopping_thresh [int]: Number of iterations without improvement before returning
            params [dict]: Specify hyperparameters for selected algorithm **IF USING 'importance', ALGORITHM MUST HAVE .feature_importances_
            cv [int] : Number of folds for cross validation, default: 5
            sample_size [float]: Percentage of features to select for model training with random selection method
            drop_size [int] : Number of features to drop with each pass, large feature sets --> may want to drop more features to save time
            correlation_tolerance [float] : Level of tolerance for correlated features
            corr_lower_by [float] : Amount to lower correlation tolerance in each iteration. Default: 0.1
            correlation_strategy [str] : How to approach removing correlated features. Acceptable arguments:
                'flat' : Flat, use drop_size parameter same as feature importance to remove n most correlated in each iteration
                'tol' : Tolerance, use correlation_tolerance parameter and remove a feature from all feature sets over correlation tolerance
            n_iterations [int] : Number of rounds of random feature selection to perform.
            n_jobs [int] : Number of processors to use. Default: None, all processors
            verbose [int]: level of status updates from object. Acceptable values:
                0 : No updates
                1 : Update when finished running
                2 : Update afer each iteration
    '''

    def recursive_selection(self):
        ''' 
        One of two top level methods of FeatureSelector object. Offers 
            Args: 
                None
            Returns: 
                None
        '''
        self.frame_prep()

        if self.early_stopping:

            no_improvement = 0

            while True:

                self.recursive_cv()

                if self.current_eval >= self.best_eval:

                    self.best_subset = self.current_subset

                    self.best_eval = self.current_eval

                    no_improvement = 0
                else:

                    no_improvement += 1

                if self.method == 'importance' or self.method == 'both':

                    if self.drop_size > len(self.importance_frame):

                        return('Cannot reduce feature frame anymore. Reduce drop size if desired')
                if no_improvement < self.stopping_thresh:

                    bottom_ = self.frame_reduction()

                    if len(bottom_) == 0:

                        return('Improvement has stopped. Check .best_subset and .best_eval')

                    self.X = self.X.drop(columns = bottom_)

                    if self.verbose == 2:

                        print('{} features have been dropped, moving to next iteration'.format(len(bottom_)))
                else:

                    return('Improvement has stopped. Check .best_subset and .best_eval')
        else:
            while True:

                self.recursive_cv()

                if self.current_eval >= self.best_eval:

                    self.best_subset = self.current_subset

                    self.best_eval = self.current_eval

                if self.drop_size > len(self.importance_frame):

                    return('Cannot reduce feature frame anymore. Reduce drop size if desired')
                bottom_ = self.frame_reduction()

                try:

                    self.X = self.X.drop(columns = bottom_)

                except:

                    return('Cannot reduce feature frame anymore. Reduce drop size if desired')

                if self.verbose == 2:

                    print('{} features have been dropped, moving to next iteration'.format(len(bottom_)))

    def random_selection(self):
        ''' 
        Second top level method for FeatureSelector object. Performs random search of feature subsets and records performance metrics for each
        subset.
        '''
        self.frame_prep()

        for j in range(self.n_iterations):

            self.random_cv()

            self.performance_log['iteration_number'] = j

            self.performance_log['feature_subset'] = self.current_subset

            self.performance_log['score'] = self.current_eval

            if self.current_eval > self.best_eval:

                self.best_eval = self.current_eval

                self.best_subset = self.current_subset

            if self.verbose == 2:

                print('Last subset score: {}. Moving to next iteration'.format(self.current_eval))

        print('Random search complete, best score was: {}'.format(self.best_eval))
         
    def recursive_cv(self):
        ''' 
        Perform cross-fold valiation and generate mean feature importances / mean score for current subset of features. Makes use of 
        concurrent.futures.PoolProcessExecutor to spread out CPU intensive algorithm training. 
            Args:
                None
            Returns:
                None
            Updates self.importance_frame: pandas Dataframe object ranking feature importances
        '''
        self.current_eval = 0

        tuple_list = []

        self.current_subset = self.X.columns

        if len(self.current_subset) == 0:

            return('Cannot reduce frame anymore. Check best eval')

        self.feature_importances = np.zeros(len(self.current_subset))

        kf = KFold(n_splits = self.cv)

        with ProcessPoolExecutor(max_workers = self.n_jobs) as executor:

            for train, test in kf.split(self.X):

                x_train, x_test = self.X.iloc[train], self.X.iloc[test]

                y_train, y_test = self.y.iloc[train], self.y.iloc[test]

                tuple_list.append(executor.submit(self.fit_train_test, x_train, x_test, y_train, y_test, self.algorithm, self.cv, 
                self.metric, self.method, params = self.params))

        if self.method == 'importance' or self.method == 'both':

            for pair in tuple_list:

                self.current_eval += pair.result()[0]

                self.feature_importances += pair.result()[1]

            self.importance_frame = pd.DataFrame({'feature' : self.current_subset, 'importance' : self.feature_importances})

            self.importance_frame = self.importance_frame.sort_values(by = ['importance'], ascending = False).reset_index(drop = True)

        else:
            for score in tuple_list:

                self.current_eval += score.result()
        
    def random_cv(self):
        ''' 
        Method to perform cross-fold validation using randomly generated subsets of features. Key difference between random_cv and recursive_cv
        is that random_cv does not effect primary dataframe X, but rather makes a copy, X_reduced, using a subset of the features, and then 
        performs cross validation on the copy. This is important because this method is not recursive, and thus the full set of features will be 
        randomly sampled during each iteration. 
            Args:
                None
            Returns:
                None
        '''
        self.current_eval = 0

        eval_list = []

        self.current_subset = self.generate_subsets(self.X.columns, self.sample_size)

        self.X_reduced = self.X[self.current_subset]

        kf = KFold(n_splits = self.cv)

        with ProcessPoolExecutor(max_workers = self.n_jobs) as executor:

            for train, test in kf.split(self.X_reduced):

                x_train, x_test = self.X_reduced.iloc[train], self.X_reduced.iloc[test]

                y_train, y_test = self.y.iloc[train], self.y.iloc[test]

                eval_list.append(executor.submit(self.fit_train_test, x_train, x_test, y_train, y_test, self.algorithm, self.cv,
                self.metric, self.method, params = self.params))

        for score in eval_list:

            self.current_eval += score.result()

    def frame_reduction(self):
        ''' 
        Method to generate list of features to be dropped before next iteration. 
            Args:
                None
            Returns:
                bottom_ [list] : list of features to be dropped
        '''
        if self.method == 'importance':

            if len(self.importance_frame[self.importance_frame.importance == 0]) != 0:

                bottom_ = list(self.importance_frame[self.importance_frame.importance == 0].feature.values)

            else:

                cutoff = (-1 * self.drop_size) - 1

                bottom_ = list(self.importance_frame.feature.iloc[-1:cutoff:-1])

        elif self.method == 'corr':

            bottom_ = self.get_correlated(self.X, self.correlation_tolerance, self.drop_size, self.correlation_strategy)

            if self.correlation_strategy == 'tol':

                self.correlation_tolerance -= self.corr_lower_by

            else:

                pass

        elif self.method == 'both':

            if len(self.importance_frame[self.importance_frame.importance == 0]) != 0:

                bottom_ = list(self.importance_frame[self.importance_frame.importance == 0].feature.values)

            else:

                cutoff = (-1 * self.drop_size) - 1

                bottom_ = list(self.importance_frame.feature.iloc[-1:cutoff:-1])

            drop_ = self.get_correlated(self.X, self.correlation_tolerance, self.drop_size, self.correlation_strategy)

            if self.correlation_strategy == 'tol':

                self.correlation_tolerance -= self.corr_lower_by

            else:

                pass

            bottom_ += drop_

            bottom_ = list(dict.fromkeys(bottom_)) #drop potential duplicates from features to drop

        else:

            raise ValueError('You have entered a method that is not valid, please select a valid method')

        return(bottom_)

    def frame_prep(self):
        ''' 
        Prepare dataframe if called for - scale features, remove VIF, drop correlated, etc.
        '''
        if self.scale:

            self.scale_features()

        if self.VIF:

            self.recursive_VIF()

        if self.drop_corr:

            _drop = self.get_correlated(self.X, self.correlation_tolerance, self.drop_size, self.correlation_strategy)

            self.X = self.X.drop(columns = _drop)



    def scale_features(self):
        ''' 
        Scale feature frame based on value provided in __init__
        '''
        cols = self.X.columns

        if self.scale == 'standard':

            XS = StandardScaler().fit_transform(self.X)

            self.X = pd.DataFrame(XS)

            self.X.columns = cols

        elif self.scale == 'minmax':

            XM = MinMaxScaler().fit_transform(self.X)

            self.X = pd.DataFrame(XM)

            self.X.columns = cols

    def recursive_VIF(self):
        ''' 
        Method to remove features over a set threshold for Variance Inflation Factor. note: adding column of constants is necessary to properly apply
        variance inflation factor function.
        '''
        dummies = self.get_dummies(self.X)

        dummy_df = self.X[dummies]

        self.X = self.X.drop(columns = dummies)

        while True:

            self.X = self.X.assign(constant = 1)

            X_cols = list(self.X.columns)

            npX = np.array(self.X)

            vif = [variance_inflation_factor(npX, i) for i in np.arange(npX.shape[1])]

            vif_ = pd.Series(vif, index = X_cols)

            vif_ = vif_.drop('constant')

            max_vif = vif_.idxmax()

            if vif_.max() > self.VIF_tol:

                self.X = self.X.drop(columns = [max_vif, 'constant'])

                if self.verbose == 2:

                    print('{} has been dropped'.format(max_vif))

            else:
                self.X = self.X.drop(columns = ['constant'])

                self.X = pd.concat([self.X, dummy_df], axis = 1)
                return
    
    @staticmethod
    def fit_train_test(x_train, x_test, y_train, y_test, algorithm, cv, metric, method, params = None):
        ''' 
        Factory method to fit, predict, and test on each cross-validation fold
        Args:
            x_train, x_test, y_tran, y_test [pd.DataFrame]: training and test spits generated by KFold splits
            algorithm [func] : algorithm used in training/testing. Passed in __init__, must have .feature_importances_ attribute
            cv [int] : number of folds for cross-validation, passed in __init__
            metric [str] : scoring metric to evaluate model performance, passed in __init__
            params [dict] : parameter dictionary to initialize algorithm, none will use default parameters
        Returns:
            score [float] : scoring metric applied to model predictions
            feature_importance [np.ndarray] : feature importances for given subset
        '''
        if params:

            algo = algorithm.set_params(**params)

        else:
            algo = algorithm

        algo.fit(x_train, y_train)

        y_pred = algo.predict(x_test)

        if metric == 'acc':

            score = accuracy_score(y_test, y_pred) / cv

        elif metric == 'precision':

            score = precision_score(y_test, y_pred) / cv

        elif metric == 'f1':

            score = precision_score(y_test, y_pred) / cv

        elif metric == 'rmse':

            score = mean_squared_error(y_test, y_pred) / cv

        elif metric == "roc":

            score = roc_auc_score(y_test, y_pred) / cv

        else:

            raise ValueError('Metric is not supported, only acc, precision, f1, roc_auc, and rmse')

        if method == 'importance' or method == 'both':  

            try:  
                
                feature_importance = algo.feature_importances_ / cv

            except:

                feature_importance = algo.coef_

            else:

                raise AttributeError("Algorithm does not support feature_importances_ or coef_")

            return( (score, feature_importance) )
        else:
            return( (score) )

    @staticmethod
    def get_correlated(X, correlation_tolerance, drop_size, strategy):
        ''' 
        Factory method to return a list of features that have high correlations to other features in the DataFrame. 
            Args: 
                X [pd.DataFrame]: Feature frame
                correlation_tolerance [float] : tolerated feature frame correlation, passed in __init__
                drop_size [int] : Number of features to remove in each iteration
                strategy [str] : Which recursion strategy to use, 'r' for removal by integer count or 'tol' for removal by tolerance
            Returns:
                [list] : list of features to be dropped
        '''
        drop_list = []

        X_corr = X.corr().abs()

        all_correlated = X_corr.where(np.triu(np.ones(X_corr.shape), k = 1).astype(np.bool))\
            .stack().sort_values(ascending = False)

        if strategy == 'tol':

            over_tol_ = all_correlated[all_correlated.values > correlation_tolerance]

            for j in range(len(over_tol_)):

                if over_tol_.index[j][1] not in drop_list:

                    drop_list.append(over_tol_.index[j][1])

        elif strategy == 'flat':

            for j in range(drop_size):

                if all_correlated.index[j][1] not in drop_list:

                    drop_list.append(all_correlated.index[j][1])
        else:

            raise ValueError('Invalid value for correlation_strategy has been passed, only accepts "r" or "tol"')

        return(drop_list)

    @staticmethod
    def generate_subsets(features, sample_size):
        ''' 
        Factory method to randomly generate subsets of features.
            Args:
                - features [list] : List of column names of features
                - sample_size [float] : Floating point number between 0 and 1, percentage of features to sample
            Returns:
                - subset [list] : list of features to sample from main DataFrame
        '''
        if sample_size <= 0 or sample_size > 1:

            raise ValueError('Sample size cannot be greater than 1 or less than or equal to 0. Select value between 0 and 1')
        subset_indices = []

        subset = []

        batch_size = sample_size * len(features)

        while len(subset_indices) < batch_size:

            indice = np.random.randint(0, len(features))

            if indice not in subset_indices:

                subset_indices.append(indice)

        for i in subset_indices:

            subset.append(features[i])

        return(subset)

    @staticmethod
    def get_dummies(X):
        ''' 
        Factory method to determine if variables are binary / dummy variables. This is necessary to calculate VIF.
        Args:
            X [pd.DataFrame] : pandas dataframe object
        Returns:
            [list] : list of feature names for dummy variables. 
        '''
        dummy_list = []

        for col in X.columns:

            if len(X[col].unique()) <= 2:

                dummy_list.append(col)

        return(dummy_list)