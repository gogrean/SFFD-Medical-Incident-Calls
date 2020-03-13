import datetime as dt

import pickle
import numpy as np
import pandas as pd
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
                         GMapOptions, \
                         HoverTool, \
                         LogColorMapper, \
                         LinearColorMapper, \
                         LogTicker, \
                         BasicTicker, \
                         FixedTicker, \
                         ColorBar
from bokeh.transform import linear_cmap, log_cmap
from bokeh.layouts import layout

from code.key_utils import get_secret_key
from code.flaskr import app
from code.db_model import db, \
                          connect_to_db, \
                          MedicalCall, \
                          TractGeometry
from code.mappings import AMBULANCE_UNITS, \
                          PRIORITY_CODES, \
                          GROUPING_FREQ, \
                          SQM_TO_100000SQFOOT
from code.tract_tools import get_tract_geom


GMAP_API_KEY = get_secret_key('GMAP_API_KEY')

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
            tmp_lng, tmp_lat = [], []
            # a non-Pythonic way to check for null geometries, since objects
            # of type WKBElement do not support boolean operations
            if tract_geom is None:
                tmp_lng.append([])
                tmp_lat.append([])
            else:
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

    @staticmethod
    def _filter_med_calls(tract, year):
        """Query the medical call table for given tract and year, and return
        incident response times."""
        response_times_tmp = db.session.query(
            MedicalCall.received_dttm,
            MedicalCall.onscene_dttm - MedicalCall.received_dttm,
        ).filter(
            MedicalCall.unit_type.in_(AMBULANCE_UNITS) &
            MedicalCall.original_priority.in_(PRIORITY_CODES)
        ).filter(
            MedicalCall.tract == tract
        ).filter(
            extract('year', MedicalCall.received_dttm) == year
        ).all()

        # convert response time to minutes and exclude values greater than
        # 30 minutes
        response_times_in_minutes = [
                (rt[0], round(rt[1].seconds / 60., 2))
                    for rt in response_times_tmp
                    if rt[1] and rt[1] < dt.timedelta(minutes=30)
        ]

        # create a dataframe out of the list of tuples returned by the
        # SQLAlchemy query; the dataframe is indexed by call date
        df = pd.DataFrame(
            response_times_in_minutes,
            columns=[
                'Date',
                'Response Time',
            ]
        ).set_index('Date')

        return df

    def _build_year_dict(self, tract_dict):
        """Construct a dictiory indexed by year with the appropriate statistics
        for each tract.

        This dictionary will be used to generate the ColumnDataSource objects
        used to plot tract patches on the Google map. It is indexed by year,
        to easily map the appropriate statistics for the user-selected year."""
        year_dict = {}
        for yr in range(self.min_year, self.max_year + 1):
            year_dict[yr] = {}
            for tract in tract_dict:
                year_dict[yr][tract] = {}
                med_calls = self._filter_med_calls(tract, yr)
                year_dict[yr][tract] = {
                    'median_response_time': float(med_calls.median()),
                    'num_incidents': med_calls.size
                }

        return year_dict

    def _build_data_source(
        self,
        year=2019,
        tract_dict=None,
        year_dict=None,
    ):
        """Build dictionary for the ColumnDataSource object in Bokeh."""
        land_tracts = [
            tr
            for tr in tract_dict
            if tract_dict[tr]['aland10']
        ]

        source_dict = dict(
            x = [
                c for tr in land_tracts
                    for c in tract_dict[tr]['lng']
            ],
            y = [
                c for tr in land_tracts
                    for c in tract_dict[tr]['lat']
            ],
            tract_name = [
                n for tr in land_tracts
                  for n in [tr]*len(tract_dict[tr]['lng'])
            ],
            response_time = [
                t if t > 0 else 0 for t in
                    [
                        rt for tr in land_tracts
                            for rt in [
                                year_dict[year][tr]['median_response_time']
                            ] * len(tract_dict[tr]['lng'])
                    ]
            ],
            num_incidents = [
                ni for tr in land_tracts
                    for ni in [
                        year_dict[year][tr]['num_incidents'] /
                            tract_dict[tr]['aland10'] * SQM_TO_100000SQFOOT
                    ] * len(tract_dict[tr]['lng'])
            ],
        )
        return source_dict


    def make_maps(self,
        lng_center=-122.439308,
        lat_center=37.754899,
        zoom_level=12,
        resp_time_colorbar_min=2,
        resp_time_colorbar_max=98,
        density_colorbar_min=5,
        density_colorbar_max=95,
        density_patch_alpha=0.5,
        resptime_patch_alpha=0.5,
        figs_output_dir='',
        scripts_output_dir='',
        div_output_dir='',
        plot_width=750,
        plot_height=600,
    ):
        """Plot maps of response time and medical incident density."""

        try:
            with open('tract_dict.p', 'rb') as f:
                tract_dict = pickle.load(f)
            with open('year_dict.p', 'rb') as f:
                year_dict = pickle.load(f)
        except:
            tract_dict = self._build_tract_dict()
            year_dict = self._build_year_dict(tract_dict)

            with open('year_dict.p', 'wb') as f:
                pickle.dump(year_dict, f)

            with open('tract_dict.p', 'wb') as f:
                pickle.dump(tract_dict, f)

        for yr in range(self.min_year, self.max_year + 1):
            density_color_map = 'Inferno256'
            tools = 'pan,wheel_zoom,reset,save'
            density_map_options = GMapOptions(
                lat=lat_center,
                lng=lng_center,
                map_type='roadmap',
                zoom=zoom_level,
            )

            col_data_source = self._build_data_source(
                year=yr,
                tract_dict=tract_dict,
                year_dict=year_dict,
            )
            col_data_source['response_time_str'] = [
                str(round(x, 1))
                    for x in col_data_source['response_time']
            ]
            col_data_source['num_incidents_str'] = [
                str(round(x, 1))
                    for x in col_data_source['num_incidents']
            ]
            source = ColumnDataSource(col_data_source)

            # ------------------------------------------------------------------
            # MAP INCIDENT DENSITY
            output_file(figs_output_dir + f"density_map_{yr}.html")

            density_plot = gmap(
                GMAP_API_KEY,
                density_map_options,
                width=750,
                height=600,
                tools=tools,
                toolbar_location='above'
            )

            tooltips = """
                   <div style="width: 13em; heigh: 3em; word-wrap: break-word;
                               margin: 0px 0px 0px 5px">
                     <div>
                       <span style="font-size: 13px; color: #A9A9A9; background-color: #FFFFFF;">
                           Medical Incident Density
                       </span>
                     </div>

                     <div style="margin-top:0.5em;">
                       <span style="font-size: 13px; color: #000000; background-color: #FFFFFF;">
                               <b>Tract @tract_name</b>
                            <br>
                               @num_incidents_str per 100,000 sq feet
                       </span>
                     </div>
                   </div>
            """
            density_plot.add_tools(HoverTool(tooltips=tooltips))

            min_color_val = np.percentile(
                col_data_source['num_incidents'],
                density_colorbar_min,
            )
            max_color_val = np.percentile(
                col_data_source['num_incidents'],
                density_colorbar_max
            )
            color_mapper = LogColorMapper(
                palette=density_color_map,
                low=min_color_val,
                high=max_color_val,
            )

            color_bar = ColorBar(
                color_mapper=color_mapper,
                label_standoff=10,
                border_line_color=None,
                location=(1,0),
                ticker=FixedTicker(ticks=[0.2, 1, 2, 4, 8, 16, 32, 64])
            )
            density_plot.add_layout(color_bar, 'right')

            density_plot.patches(
                'x', 'y',
                source=col_data_source,
                fill_color=linear_cmap(
                    'num_incidents',
                    density_color_map,
                    min_color_val,
                    max_color_val
                ),
                fill_alpha=density_patch_alpha,
                line_color="black",
                line_width=1
            )

            density_plot.yaxis.major_label_text_font_size = '10pt'
            density_plot.xaxis.major_label_text_font_size = '10pt'

            color_bar.major_label_text_font_size = '12pt'
            color_bar.major_label_text_font_style = 'italic'

            save(density_plot)

            script, div = components(density_plot)

            with open(
                scripts_output_dir + f"density_map_script_{yr}.js", 'w'
            ) as f:
                f.write(script)

            with open(
                div_output_dir + f"density_map_div_{yr}.html", 'w'
            ) as f:
                f.write(div)

            # ------------------------------------------------------------------
            # MAP RESPONSE TIMES
            output_file(figs_output_dir + f"resp_time_map_{yr}.html")

            resptime_map_options = GMapOptions(
                lat=density_map_options.lat,
                lng=density_map_options.lng,
                map_type='roadmap',
                zoom=density_map_options.zoom,
            )

            resptime_plot = gmap(
                GMAP_API_KEY,
                resptime_map_options,
                width=plot_width,
                height=plot_height,
                tools=tools,
                toolbar_location='above',
            )

            tooltips = """
                   <div style="width: 12em; heigh: 3em; word-wrap: break-word;
                               margin: 0px 0px 0px 5px">
                     <div>
                       <span style="font-size: 13px; color: #A9A9A9; background-color: #FFFFFF;">
                           Median Response Time
                       </span>
                     </div>

                     <div style="margin-top:0.5em;">
                       <span style="font-size: 13px; color: #000000; background-color: #FFFFFF;">
                               <b>Tract @tract_name</b>
                            <br>
                               @response_time_str minutes
                       </span>
                     </div>
                   </div>
            """
            resptime_plot.add_tools(HoverTool(tooltips=tooltips))

            source = ColumnDataSource(col_data_source)

            resptime_color_map = 'Inferno256'
            min_color_val = np.percentile(
                col_data_source['response_time'],
                resp_time_colorbar_min,
            )
            max_color_val = np.percentile(
                col_data_source['response_time'],
                resp_time_colorbar_max,
            )
            color_mapper = LinearColorMapper(
                palette=resptime_color_map,
                low=min_color_val,
                high=max_color_val,
            )

            color_bar = ColorBar(
                color_mapper=color_mapper,
                ticker=BasicTicker(),
                label_standoff=10,
                border_line_color=None,
                location=(1,0),
            )
            resptime_plot.add_layout(color_bar, 'right')

            resptime_plot.patches(
                'x', 'y',
                source=col_data_source,
                fill_color=linear_cmap(
                    'response_time',
                    resptime_color_map,
                    min_color_val,
                    max_color_val
                ),
                fill_alpha=resptime_patch_alpha,
                line_color="black",
                line_width=1
            )

            resptime_plot.yaxis.major_label_text_font_size = '10pt'
            resptime_plot.xaxis.major_label_text_font_size = '10pt'

            color_bar.major_label_text_font_size = '12pt'
            color_bar.major_label_text_font_style = 'italic'

            save(resptime_plot)

            script, div = components(resptime_plot)

            with open(
                scripts_output_dir + f"resp_time_map_script_{yr}.js", 'w'
            ) as f:
                f.write(script)

            with open(
                div_output_dir + f"resp_time_map_div_{yr}.html", 'w'
            ) as f:
                f.write(div)
