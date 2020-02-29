import yaml
import pandas as pd
import holidays
from joblib import load
import numpy as np
from geoalchemy2.shape import to_shape

from code.mappings import WEEKEND_DAYS, \
                          PRIORITY_CODES, \
                          AMBULANCE_UNITS, \
                          TRIG_PARAMS, \
                          DEGREES_TO_MILES
from code.location_tools import get_locations_as_shape


def _evaluate_circular_feature(
    raw_feature,
    param,
):
    """Return the sin/cos of a circular time feature.

    Parameter `param` can be 'hour', 'day_of_week', or 'day of year'."""

    feature_in_radians = 2. * np.pi * raw_feature / TRIG_PARAMS[param]
    return (
        np.sin(feature_in_radians), np.cos(feature_in_radians)
    )


def set_time_features(df,
                      flag_weekends=True,
                      flag_holidays=True,
                      country='US',
                      prov=None,
                      state='CA',
                    ):
    """Split the date into year, day of year, day of the week, and hour."""
    df['Year'] = pd.DatetimeIndex(df['Received DtTm']).year

    # The hour, day of the week, and the day of the year are circular features.
    # For example, in the case of hours, 23:30 is closer to 00:10 than 00:10 is
    # to 3:00, but by encoding the hour as given, this circularity is missed.
    # Instead, the circular features are split into (sin, cos) vector
    # components; e.g., hour features are calculated on a unit circle where the
    # angle of a point on the circle corresponds to the hour, and the hour
    # 24:00 corresponds to 2pi.

    # subtract 1 to have the days start at 0 and end at 365
    # (for leap years; or 364 otherwise)
    day_of_year = df['Received DtTm'].dt.dayofyear - 1
    df['Day_of_Year_sin'], df['Day_of_Year_cos'] = _evaluate_circular_feature(
        day_of_year,
        param='day_of_year',
    )

    day_of_week = df['Received DtTm'].dt.weekday
    df['Day_of_Week'] = day_of_week
    df['Day_of_Week_sin'], df['Day_of_Week_cos'] = _evaluate_circular_feature(
        day_of_week,
        param='day_of_week',
    )

    hour = df['Received DtTm'].dt.hour + df['Received DtTm'].dt.minute / 60.
    df['Hour_sin'], df['Hour_cos'] = _evaluate_circular_feature(
        hour,
        param='hour',
    )

    if flag_weekends:
        df = set_weekends(df)

    if flag_holidays:
        df = set_holidays(
                df,
                country=country,
                prov=prov,
                state=state,
            )

    df.drop('Received DtTm', axis=1, inplace=True)

    return df


def set_weekends(df):
    """Flag calls received on weekends."""
    is_weekend_func = lambda d: 1 if d in WEEKEND_DAYS else 0
    df['is_weekend'] = df['Day_of_Week'].apply(is_weekend_func)

    df.drop('Day_of_Week', axis=1, inplace=True)

    return df


def set_holidays(df, country='US', state='CA', prov=None):
    """Flag holidays received on weekends."""
    holiday_list = holidays.CountryHoliday(country, prov=prov, state=state)

    is_holiday_func = lambda dttm: 1 if dttm in holiday_list else 0
    df['is_holiday'] = df['Received DtTm'].apply(is_holiday_func)

    return df


def set_new_incident_priority_code(priority):
    """Set the values of the priority code parameters for a new incident.

    Each priority code parameter is set to 1 or 0, depending on an incident's
    priority code. For example, for a code 2 incident, 'Original Priority_2'
    would be set to 1, while 'Original Priority_3' would be set to 0.

    The attribute `priority_code` is read from the user's selection on the
    homepage, and has the form, e.g., 'priority-3'; the last character is the
    actual priority code.
    """

    return {f"Original Priority_{pc}": int(priority[-1].upper() == pc)
            for pc in PRIORITY_CODES}


def set_new_incident_unit_type(unit_type):
    """Set the values of the unit type parameters for a new incident."""
    return dict(
        [
            (f"Unit Type_{ut}", int(unit_type.upper() == ut))
                for ut in AMBULANCE_UNITS
        ]
    )


def get_shortest_distance(location, pts=None):
    """Return the shortest distance between a location and a set of points."""
    return min([location.distance(pt) for pt in pts])


def find_dist_to_closest_fire_station(df, pts):
    """Calculate the distance to the closest fire station."""

    # calculate the closest fire station for each incident;
    # result is in degrees
    df['Nearest Fire Station'] = df['Coords'].apply(lambda x:
        get_shortest_distance(x, pts=pts)
    )

    # convert the result to miles
    df['Nearest Fire Station'] *= DEGREES_TO_MILES

    return df


def find_dist_to_closest_hospital(df, pts):
    """Calculate the distance to the closest hospital."""

    # calculate the closest fire station for each incident;
    # result is in degrees
    df['Nearest Hospital'] = df['Coords'].apply(lambda x:
        get_shortest_distance(x, pts=pts)
    )

    # convert the result to miles
    df['Nearest Hospital'] *= DEGREES_TO_MILES

    return df


def set_lon_lat_from_shapely_point(df):
    """Set longitude and latitude columns from the POINT coordinates."""
    df['Latitude'] = df['Coords'].apply(lambda c: c.y)
    df['Longitude'] = df['Coords'].apply(lambda c: c.x)

    df.drop('Coords', axis=1, inplace=True)

    return df


def load_model(filename):
    """Load a fitted scikit-learn model from the given filename."""
    return load(filename)


def predict_eta(df, filename='rf_model.joblib', model=None):
    """Predict the arrival time of an ambulance using a given model.

    The model can be read from a joblib file, or can be passed directly to
    the function."""
    if filename:
        m = load_model('rf_model.joblib')
        return m.predict(df)[0]
    elif model:
        raise Warning("Sorry, this is not implemented yet...")
    else:
        raise Warning("Either the `filename` or the `model` parameters must be provided.")
