import yaml
import pandas as pd
import holidays
from joblib import load

from code.mappings import WEEKEND_DAYS, \
                          PRIORITY_CODES, \
                          AMBULANCE_UNITS


def get_secret_key(key_name, key_fp="../credentials/keys.yml"):
    """Read a key from a YAML file."""

    with open(key_fp, 'r') as f:
        credentials = yaml.load(f, Loader=yaml.FullLoader)

    return(credentials[key_name])


def set_time_features(df,
                      flag_weekends=True,
                      flag_holidays=True,
                      country='US',
                      prov=None,
                      state='CA',
                    ):
    """Split the date of a call into year, month, day of the week, and hour."""
    df['Year'] = pd.DatetimeIndex(df['Received DtTm']).year
    df['Month'] = pd.DatetimeIndex(df['Received DtTm']).month
    df['Day_of_Week'] = pd.DatetimeIndex(df['Received DtTm']).weekday
    df['Hour'] = [
        round(t.hour + t.minute/60.)
        for t in pd.DatetimeIndex(df['Received DtTm']).time
    ]

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

    return df


def set_holidays(df, country='US', state='CA', prov=None):
    """Flag holidays received on weekends."""
    holiday_list = holidays.CountryHoliday(country, prov=prov, state=state)

    is_holiday_func = lambda dttm: 1 if dttm in holiday_list else 0
    df['is_holiday'] = df['Received DtTm'].apply(is_holiday_func)

    return df


def set_new_incident_priority_code(priority):
    """Set the values of the priority code parameters for model fitting.

    Each priority code parameter is set to 1 or 0, depending on an incident's
    priority code. For example, for a code 2 incident, 'Original Priority_2'
    would be set to 1, while 'Original Priority_3' would be set to 0.

    The attribute `priority_code` is read from the user's selection on the
    homepage, and has the form, e.g., 'priority-3'; the last character is the
    actual priority code.
    """
    return dict(
        [
            (f"Original Priority_{pc}", int(priority[-1].upper() == pc))
                for pc in PRIORITY_CODES
        ]
    )


def set_new_incident_unit_type(unit_type):
    return dict(
        [
            (f"Unit Type_{ut}", int(unit_type.upper() == ut))
                for ut in AMBULANCE_UNITS
        ]
    )


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
