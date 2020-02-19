import datetime as dt

import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder

from sf_data import get_medical_calls


def filter_features(filename):
    """Filter out columns that will not be used in the ML model."""

    full_med_calls_df = get_medical_calls(filename=filename)
    del_columns = ['Call Number', 'Unit ID', 'Incident Number', 'Call Type',
                   'Call Date', 'Watch Date', 'Entry DtTm', 'Dispatch DtTm',
                   'Response DtTm', 'Transport DtTm', 'Hospital DtTm',
                   'Call Final Disposition', 'Available DtTm', 'Address',
                   'City', 'Zipcode of Incident', 'Battalion', 'Station Area',
                   'Box', 'Priority', 'Final Priority', 'ALS Unit',
                   'Call Type Group', 'Number of Alarms',
                   'Unit sequence in call dispatch', 'Fire Prevention District',
                   'Supervisor District',
                   'Neighborhooods - Analysis Boundaries', 'Location', 'RowID']
    filtered_df = full_med_calls_df.drop(del_columns, axis=1)

    return filtered_df


def get_response_time(filename):
    """Calculate the ambulance response time for each incident.

    Only the fire department and private ambulance responses are included. The
    response times are returned in minutes."""

    filtered_df = filter_features(filename)

    # only interested in the ambulance ('Unit Type' listed as 'MEDIC' or
    # 'PRIVATE') response time, rather then response time for fire trucks, etc.
    filtered_df = filtered_df[filtered_df['Unit Type'].isin(['MEDIC', 'PRIVATE'])]

    # calculate the response time as the difference between the time a
    # unit arrives on scene and the time when the emergency call was received
    filtered_df['Response Time'] = filtered_df['On Scene DtTm'] - \
                                   filtered_df['Received DtTm']

    # convert the response time from nanoseconds to minutes
    filtered_df['Response Time'] /= (1e9*60)

    # the 'On Scene DtTm' is no longer needed
    filtered_df.drop('On Scene DtTm', axis=1, inplace=True)

    return filtered_df


def filter_by_response_time(filename='Med_Calls_with_Tracts.pkl'):
    """Filter out very large (likely incorrect) and negative response times."""

    df = get_response_time(filename=filename)

    # remove NaN values caused by NaN 'On Scene DtTm',
    # since there are few of them -- these are the only NaN values, hence no
    # filtering by column before dropping
    df.dropna(inplace=True)

    # remove erroneous entries in which the response time is negative
    df = df[df['Response Time'] > dt.timedelta()]

    # remove very large response times (>99 percentile)
    #
    # TODO: Understand why for a small fraction of the calls, the response
    # time is very large. The 99% cuts it off at about 35 minutes using the
    # data up to early December 2019.
    response_time_cutoff = np.percentile(df['Response Time'], 99)
    filtered_df = df[df['Response Time'] < response_time_cutoff]

    return filtered_df
