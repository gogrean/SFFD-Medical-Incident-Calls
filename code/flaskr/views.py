import datetime as dt

import pandas as pd
from flask import render_template, request, jsonify, flash, redirect, url_for
from shapely.geometry import Point

from code.flaskr import app
from code.db_model import SFHospital, \
                          SFFDFireStation
from code.mappings import US_STATE_ABBR, \
                          AMBULANCE_UNITS, \
                          FEATURE_COLS
from code.location_tools import get_new_incident_coords, \
                                get_new_incident_tract, \
                                get_locations_as_shape
from code.utils import set_time_features, \
                       load_model, \
                       set_new_incident_priority_code, \
                       set_new_incident_unit_type, \
                       predict_eta, \
                       find_dist_to_closest_hospital, \
                       find_dist_to_closest_fire_station, \
                       get_fig_components
from code.key_utils import get_secret_key


CODE_DIR = get_secret_key('CODE_DIR')
FLASK_DIR = f"{CODE_DIR}/flaskr/"


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route('/about')
def about():
    """About page."""

    return render_template("about.html")


@app.route('/stats')
def show_stats():
    """Display the statistics page."""

    return render_template("stats.html")


@app.route('/response-times')
def show_resp_time_map():
    """Display the response time maps."""

    DEFAULT_YEAR = '2019'

    return render_template(
        "resp_time_map.html",
        default_year=DEFAULT_YEAR,
    )


@app.route('/incident-density')
def show_incident_density_map():
    """Display the incident density maps."""

    DEFAULT_YEAR = '2019'

    return render_template(
        "incident_density_map.html",
        default_year=DEFAULT_YEAR,
    )


@app.route('/tract-stats')
def get_tract_stats():
    """Display the tract statistics."""
    # get the location from the user input
    location = request.args['location']

    lng, lat, city, state = get_new_incident_coords(location)
    print(lng, lat)
    if not lng or not lat:
        return jsonify(
            js_func='',
            div_tag='',
            error_msg="""
                <div class="alert alert-warning alert-dismissible" role="alert">
                  <button type="button"
                          class="close"
                          data-dismiss="alert"
                          aria-label="Close">
                  </button>
                  <span><strong>Can't retrieve statistics. Address not found!</strong></span>
                </div>
            """,
        )

    tract = get_new_incident_tract(lng, lat)

    div_tag, js_func = get_fig_components(
        div_filepath=f'{FLASK_DIR}/templates/stats_pages/stats_div_tract{tract}.html',
        js_filepath=f'{FLASK_DIR}/static/js/stats_script_tract{tract}.js',
    )

    return jsonify(
        js_func=js_func,
        div_tag=div_tag,
        error_msg=None,
    )


@app.route('/resp-time-map')
def get_resp_time_map():
    """Display the response time distribution."""
    # get the year from the user input
    year = request.args['year']

    div_tag, js_func = get_fig_components(
        div_filepath=f'{FLASK_DIR}/templates/stats_pages/resp_time_map_div_{year}.html',
        js_filepath=f'{FLASK_DIR}/static/js/resp_time_map_script_{year}.js',
    )

    return jsonify(
        js_func=js_func,
        div_tag=div_tag,
    )


@app.route('/incident-density-map')
def get_incident_density_map():
    """Display the incident density distribution."""
    # get the year from the user input
    year = request.args['year']

    div_tag, js_func = get_fig_components(
        div_filepath=f'{FLASK_DIR}/templates/stats_pages/density_map_div_{year}.html',
        js_filepath=f'{FLASK_DIR}/static/js/density_map_script_{year}.js',
    )

    return jsonify(
        js_func=js_func,
        div_tag=div_tag,
    )


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
    if not lng or not lat:
        return jsonify(
            success='',
            error_msg="""
                <div class="alert alert-warning alert-dismissible" role="alert">
                  <button type="button"
                          class="close"
                          data-dismiss="alert"
                          aria-label="Close">
                  </button>
                  <span>
                    <b>
                        Can't estimated the arrival time. Address not found!
                    </b>
                  </span>
                </div>
            """,
        )
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

    # this is added separately to the dataframe, rather to the dictionary
    # used to create the dataframe, because Pandas otherwise splits the latitude
    # and longitude in 'Coords' into two separate lines of the dataframe; this
    # is a bug in Pandas, as it doesn't seem to handle shapely geometry objects
    # correctly...
    incident_df['Coords'] = Point(lng, lat)

    # take the DataFrame above and set the time features from the
    # 'Received DtTm' value
    state_abbr = US_STATE_ABBR[state]
    incident_df = set_time_features(
        incident_df,
        state=state_abbr,
    )

    # add column with distance to the closest hospital
    incident_df = find_dist_to_closest_hospital(
        incident_df,
        get_locations_as_shape(SFHospital)
    )

    # add column with distance to the closest fire station
    incident_df = find_dist_to_closest_fire_station(
        incident_df,
        get_locations_as_shape(SFFDFireStation)
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

    print(f"ESTIMATED ARRIVAL TIME: {int(round(wait_time, 0))} minutes")

    return jsonify(
        success=f"{int(round(wait_time))} minutes",
        error_msg=None,
    )
