import datetime as dt

from flask import render_template, request

from . import app

@app.route('/')
def index():
    """Homepage."""
    return render_template("homepage.html")

@app.route('/prediction')
def estimated_wait_time():
    current_DtTm = dt.datetime.now()
    priority = request.args['priority']
    unit_type = request.args['unit-type']
    print("SANITY CHECK: ", current_DtTm, priority, unit_type)
    return "Hey, this works."
