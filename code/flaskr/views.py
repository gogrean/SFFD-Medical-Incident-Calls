import datetime as dt

import pandas as pd
from flask import render_template, request

from . import app
from code.mappings import US_STATE_ABBR, \
                          AMBULANCE_UNITS, \
                          FEATURE_COLS
from code.location_tools import get_new_incident_coords, \
                                get_new_incident_tract
from code.utils import set_time_features, \
                       load_model, \
                       set_new_incident_priority_code, \
                       set_new_incident_unit_type, \
                       predict_eta


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


# TODO: Needs refactoring into smaller functions.
@app.route('/make-prediction')
def estimated_wait_time(
    filename='rf_model.joblib',
    model=None,
):
    """Predict the wait time for an ambulance.

    The prediction is made based on a fitted scikit-learn model and on the
    user's input on the homepage."""
    # get the time of the incident
    # (it is the time when the request is made)
    current_DtTm = dt.datetime.now()

    # get the address, priority, and unit type from the user input on
    # the homepage
    street_address = request.args['incident-address']
    priority = request.args['priority']
    unit_type = request.args['unit-type']

    # TODO: If (lng, lat) are None, then the app should flash a warning that
    # the address was not found.
    lng, lat, city, state = get_new_incident_coords(street_address)
    tract = get_new_incident_tract(lng, lat)

    # make a dictionary whose keys match the names of the features in the
    # RF model
    incident_dict = {
        'Received DtTm': current_DtTm,
        'Tract': tract,
        'Latitude': lat,
        'Longitude': lng,
    }

    # set the values (0 or 1) of the priority code parameters
    priority_codes_dict = set_new_incident_priority_code(priority)
    incident_dict.update(priority_codes_dict)

    # set the values (0 or 1) of the unit type parameters
    unit_type_dict = set_new_incident_unit_type(unit_type)
    incident_dict.update(unit_type_dict)

    # convert the dictionary into a Pandas DataFrame
    incident_df = pd.DataFrame(incident_dict, index=[0])

    # take the DataFrame above and set the time features from the
    # 'Received DtTm' value
    state_abbr = US_STATE_ABBR[state]
    incident_df = set_time_features(
        incident_df,
        state=state_abbr,
    )

    # columns reordered to match the training dataset
    incident_df = incident_df[FEATURE_COLS]

    # send the incident_df DataFrame to the predict_eta function to estimate
    # the arrival time for an ambulance
    wait_time = predict_eta(
        incident_df,
        filename=filename,
        model=model,
    )

    print(f"ESTIMATED ARRIVAL TIME: {round(wait_time, 1)} minutes")

    return f"{round(wait_time, 1)} minutes"
