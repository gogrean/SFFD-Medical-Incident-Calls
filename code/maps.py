from geoalchemy2.shape import to_shape
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

    @staticmethod
    def _build_tract_dict():
        all_tracts = [
            tr[0] for tr in db.session.query(
                                TractGeometry.geoid10
                            ).all()
        ]

        all_tract_land_areas = [
            tr[0] for tr in db.session.query(
                                TractGeometry.aland10
                            ).all()
        ]

        all_tract_geoms = [
            tr[0] for tr in db.session.query(
                            TractGeometry.the_geom
                        ).all()
        ]

        all_tract_lng = []
        all_tract_lat = []
        for tract_geom in all_tract_geoms:
            # a non-Pythonic way to check for null geometries, since objects
            # of type WKBElement do not support boolean operations
            if tract_geom is None:
                continue
            tmp_lng, tmp_lat = [], []
            for pg in list(to_shape(tract_geom).geoms):
                c = pg.exterior.coords.xy
                tmp_lng.append(list(c[0]))
                tmp_lat.append(list(c[1]))
            all_tract_lng.append(tmp_lng)
            all_tract_lat.append(tmp_lat)

        return {tract_id: {
                    'aland10': aland10,
                    'lng': lng,
                    'lat': lat,
                }
                for tract_id, aland10, lng, lat in zip(
                    all_tracts,
                    all_tract_land_areas,
                    all_tract_lng,
                    all_tract_lat,
                )
        }

    def make_maps(self):
        """Generate maps of response time and number of incidents."""

        tract_dict = self._build_tract_dict()

        for yr in range(self.min_year, self.max_year + 1):
            break
