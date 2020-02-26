import datetime as dt
from copy import deepcopy

import numpy as np
import pandas as pd
import holidays
from joblib import dump
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

from code.mappings import NON_FEATURE_COLS, AMBULANCE_UNITS
from code.sf_data import get_medical_calls
from code.utils import set_time_features, set_lon_lat_from_shapely_point


class RFModel:
    """Fit a random forest regression model.

    The medical calls dataframe is preproccesed before fitting. There is also
    the option of retrieving cached model parameters, as the fit takes time."""

    def __init__(
        self,
        filename='Med_Calls_with_Tracts.pkl',
        flag_holidays=True,
        country='US',
        state='CA',
        prov=None,
        flag_weekends=True,
        test_size=0.25,
        random_state_split=None,
        random_state_fit=42,
        n_estimators=250,
        min_samples_split=50,
        max_features='log2',
    ):
        """Read the pickled Pandas dataframe of medical incidents."""
        self.original_df = get_medical_calls(filename=filename)

        # this will be the preprocessed dataframe
        self.df = deepcopy(self.original_df)

        # set other data-related class attributes
        self.country = country
        self.state = state
        self.prov = prov
        self.flag_holidays = flag_holidays
        self.flag_weekends = flag_weekends

        # set model-related class attributes
        self.test_size = test_size
        self.random_state_split = random_state_split
        self.model_params_dict = {
            'random_state': random_state_fit,
            'n_estimators': n_estimators,
            'min_samples_split': min_samples_split,
            'max_features': max_features,
        }

        # remove NaN values caused by NaN 'Tract' or 'On Scene DtTm',
        # since there are only a few of them -- these are the only NaN values,
        # hence no filtering by column before dropping
        self.df.dropna(inplace=True)

        # making this an integer allows directly using the value in the ML model
        # without HotOneEncoding the Tract feature first
        self.df['Tract'] = self.df['Tract'].astype(int)

    def _filter_features(self, del_columns=NON_FEATURE_COLS):
        """Filter out columns that will not be used as model features."""
        self.df.drop(NON_FEATURE_COLS, axis=1, inplace=True)

    def _get_response_time(self):
        """Calculate the ambulance response time for each incident.

        Only the fire department and private ambulance responses are included. The
        response times are returned in minutes."""

        # only interested in the ambulance ('Unit Type' listed as 'MEDIC' or
        # 'PRIVATE') response time, rather then response time for fire trucks, etc.
        self.df = self.df[self.df['Unit Type'].isin(AMBULANCE_UNITS)]

        # calculate the response time as the difference between the time a
        # unit arrives on scene and the time when the emergency call was
        # received
        self.df['Response Time'] = (
            self.df['On Scene DtTm'] -
            self.df['Received DtTm']
        )

        # convert the response time from dt.timedelta nanoseconds to minutes
        self.df['Response Time'] = [
            x.total_seconds() / 60.
            for x in self.df['Response Time']
        ]

        # the 'On Scene DtTm' is no longer needed
        self.df.drop('On Scene DtTm', axis=1, inplace=True)

    def _filter_by_response_time(self):
        """Remove very large (likely incorrect) and negative response times."""

        # remove erroneous entries in which the response time is negative
        self.df = self.df[self.df['Response Time'] > 0]

        # remove very large response times (>99 percentile)
        #
        # TODO: Understand why for a small fraction of the calls, the response
        # time is very large. The 99% cuts it off at about 35 minutes using the
        # data up to early December 2019.
        response_time_cutoff = np.percentile(self.df['Response Time'], 99)
        self.df = self.df[self.df['Response Time'] < response_time_cutoff]

    def _get_time_features(self):
        """Set time features in the dataframe used for modeling."""

        # set the Year, Day of Year, Day of Week, and Hour columns, and
        # optionally flag holidays and weekends
        self.df = set_time_features(
            self.df,
            flag_weekends=self.flag_weekends,
            flag_holidays=self.flag_holidays,
            country=self.country,
            prov=self.prov,
            state=self.state,
        )

    def _get_lon_lat(self):
        """Set the longitude and latitude."""
        self.df = set_lon_lat_from_shapely_point(self.df)

    def _hot_one_encode(self):
        """Hot-one-encode non-numerical features."""
        self.df = pd.get_dummies(self.df)

    def preprocess(self):
        """Combine the preprocessing steps to return a dataframe for fitting."""
        self._filter_features()
        self._get_response_time()
        self._filter_by_response_time()
        self._get_time_features()
        self._get_lon_lat()
        self._hot_one_encode()

        return self.df

    def _split_data(self):
        """Split the dataset into training and testing subsets."""
        y_labels = ['Response Time']
        X_labels = [
            lbl
            for lbl in self.df.columns
            if lbl not in y_labels
        ]

        X = self.df[X_labels]
        y = self.df[y_labels]

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X,
            y,
            test_size=self.test_size,
            random_state=self.random_state_split
        )

    # TODO: Test this code. Previously ran the grid search interactively
    # in the Notebook...
    def _run_grid_search(
        self,
        distributions=DEFAULT_PARAM_DISTR_RFR,
        verbose=2,
    ):
        """Perform a grid search to find the best parameters for the model."""
        # define the estimator
        self.model = RandomForestRegressor(
            random_state = self.model_params_dict['random_state']
        )

        # define the parameter space on which the seach will be run
        self.clf = RandomizedSearchCV(
            self.model,
            distributions,
            verbose=verbose,
        )

        # fit the model using the parameter combinations defined above
        self.search = self.clf.fit(
            self.X_train,
            self.y_train.values.ravel()
        )

        # update the parameters with which the model will be fitted
        self.model_params_dict.update(self.search.best_params_)

    def fit_model(
        self,
        grid_search=False,
        distributions=DEFAULT_PARAM_DISTR_RFR,
        ):
        """Fit a RF regression model to the data."""
        self._split_data()

        if grid_search:
            self._run_grid_search(
                distributions=distributions,
                verbose=2
            )

        self.model = RandomForestRegressor(
            **self.model_params_dict
        )

        self.model.fit(
            self.X_train,
            self.y_train.values.ravel()
        )

    def save_model(self, filename='rf_model.joblib'):
        """Save the RF regression model."""
        dump(self.model, filename)
