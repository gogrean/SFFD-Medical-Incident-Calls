import datetime as dt

from flask import render_template, request

from . import app
from code.location_tools import get_new_incident_coords, \
                                get_new_incident_tract

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
    lng, lat = get_new_incident_coords(street_address)
    tract = get_new_incident_tract(lng, lat)

    return (
        "SANITY CHECK:"
        f"\t Coords: {lng} {lat}, "
        f"\t Tract: {tract}, "
        f"\t Current DtTm: {current_DtTm}, "
        f"\t Priority: {priority}, "
        f"\t Unit Type: {unit_type}"
    )
