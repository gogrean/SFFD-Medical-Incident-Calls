import datetime as dt

import pandas as pd
from flask import render_template, request

from . import app
from code.mappings import US_STATE_ABBR, \
                          PRIORITY_CODES, \
                          AMBULANCE_UNITS
from code.location_tools import get_new_incident_coords, \
                                get_new_incident_tract
from code.utils import set_time_features


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")

@app.route('/prediction')
def estimated_wait_time():
    current_DtTm = dt.datetime.now()
    street_address = request.args['incident-address']
    priority = request.args['priority']
    unit_type = request.args['unit-type']

    # TODO: If (lng, lat) are None, then the app should flash a warning that
    # the address was not found.
    lng, lat, city, state = get_new_incident_coords(street_address)
    tract = get_new_incident_tract(lng, lat)

    incident_dict = {
        'Received DtTm': current_DtTm,
        'Tract': tract,
        'Latitude': lat,
        'Longitude': lng,
    }

    priority_codes_dict = dict(
        [
            (f"Original Priority_{pc}", int(priority[-1].upper() == pc))
                for pc in PRIORITY_CODES
        ]
    )
    incident_dict.update(priority_codes_dict)

    unit_type_dict = dict(
        [
            (f"Unit Type_{ut}", int(unit_type.upper() == ut))
                for ut in AMBULANCE_UNITS
        ]
    )
    incident_dict.update(unit_type_dict)
    incident_df = pd.DataFrame(incident_dict, index=[0])

    state_abbr = US_STATE_ABBR[state]
    incident_df = set_time_features(
        incident_df,
        state=state_abbr
    )

    print(incident_df)

    return (
        "SANITY CHECK:"
        f"Coords: {lng} {lat}, "
        f"Tract: {tract}, "
        f"State: {state_abbr}, "
        f"Current DtTm: {current_DtTm}, "
        f"Priority: {priority}, "
        f"Unit Type: {unit_type}"
    )
