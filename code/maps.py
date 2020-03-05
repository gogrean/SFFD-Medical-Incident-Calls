from sqlalchemy import Integer
from sqlalchemy.sql import functions as func, \
                           extract, \
                           cast
from bokeh.plotting import figure, \
                           output_file, \
                           show, \
                           save, \
                           gmap
from bokeh.embed import components
from bokeh.models import LinearAxis, \
                         Range1d, \
                         ColumnDataSource, \
                         GMapOptions

from code.key_utils import get_secret_key
from code.flaskr import app
from code.db_model import db, \
                          connect_to_db, \
                          MedicalCall, \
                          TractGeometry
from code.mappings import AMBULANCE_UNITS, \
                          PRIORITY_CODES, \
                          GROUPING_FREQ
from code.tract_tools import get_tract_geom


class MapPlotter:
    """Plotting class for full map statistics."""

    def __init__(self):
        """Find the date range and instantiate the data dictionary."""
        connect_to_db(app)

        self.min_year = db.session.query(
            cast(func.min(extract('year', MedicalCall.received_dttm)), Integer)
        ).scalar()

        self.max_year = db.session.query(
            cast(func.max(extract('year', MedicalCall.received_dttm)), Integer)
        ).scalar()

        self.data = {}
