import datetime as dt

from flask import render_template, request

from . import app
from code.location_tools import find_me, add_city_state

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

    dispatch_loc = find_me()
    address = add_city_state(
        street_address,
        dispatch_loc['city'],
        dispatch_loc['state'],
    )

    return (
        "SANITY CHECK:"
        f"\t Address: {address}, "
        f"\t Current DtTm: {current_DtTm}, "
        f"\t Priority: {priority}, "
        f"\t Unit Type: {unit_type}"
    )
