from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from jinja2 import StrictUndefined

from code.db_model import connect_to_db
from code.key_utils import get_secret_key

app = Flask(__name__)

from code.flaskr import views

# reads the app key from a YAML file
APP_KEY = get_secret_key('APP_KEY')
app.secret_key = APP_KEY

# Raises an error in the case of an undefined variable in Jinja2.
app.jinja_env.undefined = StrictUndefined

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = False

    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
