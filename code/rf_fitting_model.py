import datetime as dt
from copy import deepcopy

import numpy as np
import pandas as pd
import holidays
from sklearn.preprocessing import OneHotEncoder

from mappings import NON_FEATURE_COLS, AMBULANCE_UNITS
from sf_data import get_medical_calls
from utils import set_time_features, set_lon_lat_from_shapely_point


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
    ):
        """Read the pickled Pandas dataframe of medical incidents."""
        self.original_df = get_medical_calls(filename=filename)

        # this will be the preprocessed dataframe
        self.df = deepcopy(self.original_df)

        # set other class attributes
        self.country = country
        self.state = state
        self.prov = prov
        self.flag_holidays = flag_holidays
        self.flag_weekends = flag_weekends

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

        # remove NaN values caused by NaN 'On Scene DtTm',
        # since there are few of them -- these are the only NaN values, hence no
        # filtering by column before dropping
        self.df.dropna(inplace=True)

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

        # set the Year, Month, Day of the Week, and Hour columns, and
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
