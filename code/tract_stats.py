import datetime as dt
import pandas as pd
from bokeh.plotting import figure, \
                           output_file, \
                           show, \
                           save, \
                           gmap
from bokeh.layouts import layout
from bokeh.embed import components
from bokeh.models import LinearAxis, \
                         Range1d, \
                         ColumnDataSource, \
                         GMapOptions
from sqlalchemy.sql import functions as func

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


GMAP_API_KEY = get_secret_key('GMAP_API_KEY')

class StatsPlotter:
    """Plotting class for tract statistics.

    Optional filtering can be done based starting date and end date. Dates are
    strings formatted as %Y-%m-%d, e.g. '2019-02-13'."""
    def __init__(self,
                 tract_id=None,
                 min_date=None,
                 max_date=None):
        connect_to_db(app)

        if not min_date:
            min_date = db.session.query(
                func.min(MedicalCall.received_dttm)
            ).first()[0]

        if not max_date:
            max_date = db.session.query(
                func.max(MedicalCall.received_dttm)
            ).first()[0]

        self.min_date = min_date
        self.max_date = max_date

        if tract_id:
            self.tract = tract_id

    @staticmethod
    def _filter_response_times(tract_id, min_date, max_date):
        """Filter response times."""
        response_times_tmp = db.session.query(
            MedicalCall.received_dttm,
            MedicalCall.onscene_dttm - MedicalCall.received_dttm,
            MedicalCall.original_priority,
        )

        response_times_tmp = response_times_tmp.filter(
            MedicalCall.unit_type.in_(AMBULANCE_UNITS) &
            MedicalCall.original_priority.in_(PRIORITY_CODES)
        )

        response_times_tmp = response_times_tmp.filter(
            MedicalCall.tract == tract_id
        )

        response_times_tmp = response_times_tmp.filter(
            MedicalCall.received_dttm >= min_date
        )

        response_times_tmp = response_times_tmp.filter(
            MedicalCall.received_dttm <= max_date
        )

        return response_times_tmp.all()

    @staticmethod
    def _get_tracts(tracts):
        """Get the tracts for which the stats will be plotted."""
        # if no tracts are given as input, the stats are plotted for
        # all the tracts in the database
        if not tracts:
            tracts = [
                tr[0] for tr in db.session.query(
                                    MedicalCall.tract
                                ).distinct().all()
                if tr[0] != 'NaN'
            ]
        # if only one tract is entered as an integer, try to make it a list
        elif not isinstance(tracts, list):
            tracts = [str(tracts)]
        # if the tracts are already a list, make sure they are strings
        else:
            tracts = [str(tr) for tr in tracts]

        return tracts

    def _get_response_time_and_priority_df(self, tract):
        """Create a dataframe with response times and priorities for the
        filtered events."""
        # query the database for the required data, filtering by tract and
        # date range
        response_times = self._filter_response_times(
            tract,
            self.min_date,
            self.max_date,
        )

        # convert the response time in minutes and, like when fitting the
        # random forest regression model, ignore response times larger
        # than 30 minutes
        response_times_in_minutes = sorted(
            [
                (rt[0], round(rt[1].seconds / 60., 2), rt[2])
                    for rt in response_times
                    if rt[1] and rt[1] < dt.timedelta(minutes=30)
            ],
            key=lambda x: x[0]
        )

        # create a dataframe out of the list of tuples returned by the
        # SQLAlchemy query; the dataframe is indexed by call date
        df = pd.DataFrame(
            response_times_in_minutes,
            columns=[
                'Date',
                'Response Time',
                'Priority',
            ]
        ).set_index('Date')

        return df

    @staticmethod
    def _group_median_response_time(df, freq):
        """Get the median response time for the given time frequency."""
        return df['Response Time'].groupby(
            pd.Grouper(freq=freq)
        ).median()

    @staticmethod
    def _group_num_incidents(df, freq):
        """Get the total number of incidents for the given time frequency."""
        return df['Response Time'].groupby(
            pd.Grouper(freq=freq)
        ).count()

    def _group_priority(self, df, freq):
        """Get the number of incidents grouped by priority for the given time
        frequency."""
        # some ugly index gymnastics is required here, because a bug in Pandas
        # groupby aggregate size & count methods excludes empty groups even
        # when the observed parameter of groupby is set to False

        # get dates between the start date and end date, at freq='D'
        dates = pd.date_range(
                start=self.min_date,
                end=self.max_date,
            )

        # date grouping is done differently by different methods, so for
        # consistency I generate a non-sense Pandas dataframe that I index by
        # date and then group in the same way the dataset queried from the
        # database was grouped; the date is extracted from the datetime objects
        # and I get a list of quartely dates
        quarterly_dates = [
            d.date() for d in pd.DataFrame(
                {
                    'date': dates,
                    '_col': range(len(dates))
                }
            ).set_index('date').groupby(
                pd.Grouper(freq=freq)
            ).indices.keys()
        ]

        # make an artificial index that includes all the time periods,
        # including those in which the aggregate count/size methods return
        # empty groups
        my_idx = pd.MultiIndex.from_product(
            [
                PRIORITY_CODES,
                quarterly_dates,
            ],
            names=[
                'Priority',
                'Date',
            ],
        )

        # return a reindexed array, with empty groups set to zero rather
        # than ignored
        return df.groupby(
            [
                'Priority',
                pd.Grouper(freq=freq)
            ]
        ).size().reindex(my_idx, fill_value=0)

    @staticmethod
    def _get_tract_geom(tract):
        """Get the geometry of the tract."""
        tract_geometry = db.session.query(
            TractGeometry.the_geom
        ).filter(
            TractGeometry.geoid10 == tract
        ).first()

        try:
            geom = to_shape(tract_geometry[0])
        except:
            print(tract_geometry, tract)
        cntr_lng, cntr_lat = geom[0].centroid.xy

        return (geom, cntr_lng[0], cntr_lat[0])

    def plot_time_evol(
        self,
        tracts=None,
        figs_output_dir='',
        scripts_output_dir='',
        div_output_dir='',
    ):
        """Plot response time and number of incidents as a function of time.

        If `tracts` is not provided, the method generates plots for each tract
        in the database. The `tracts` parameter is expected to be a list of
        strings (not zero-padded), though the method will attempt to convert
        it to the correct data type otherwise."""

        tracts = self._get_tracts(tracts)

        for tr in tracts:
            # filter dataset by date and tract
            df_tmp = self._get_response_time_and_priority_df(tr)

            median_response_time = self._group_median_response_time(
                df_tmp,
                GROUPING_FREQ,
            )

            total_num_incidents = self._group_num_incidents(
                df_tmp,
                GROUPING_FREQ,
            )

            priority_groups = self._group_priority(
                df_tmp,
                GROUPING_FREQ,
            )

            tract_geometry, cntr_lng, cntr_lat = self._get_tract_geom(tr)

            output_file(figs_output_dir + f"stats_tract{tr}.html")
            tools = "pan,wheel_zoom,box_zoom,crosshair,reset"

            p1 = figure(
                plot_width=1200,
                plot_height=400,
                x_axis_type='datetime',
                x_axis_label='Date',
                y_axis_label='Median Response Time (minutes)',
                toolbar_location="above",
                tools=tools,
            )

            p1.yaxis.axis_label_text_font_size = '12pt'
            p1.yaxis.major_label_text_font_size = '10pt'
            p1.yaxis.axis_label_text_color = 'steelblue'

            p1.xaxis.axis_label_text_font_size = '12pt'
            p1.xaxis.major_label_text_font_size = '10pt'

            p1.line(
                median_response_time.index,
                median_response_time.values,
                line_width=5,
                color='steelblue',
                alpha=0.75,
                legend_label='Median Response Time',
            )

            p1.y_range = Range1d(
                min(median_response_time) * 0.95,
                max(median_response_time) * 1.05,
            )

            p1.extra_y_ranges = {
                'NumIncidents': Range1d(
                    start=min(total_num_incidents) * 0.95,
                    end=max(total_num_incidents) * 1.05,
                )
            }
            p1.add_layout(
                LinearAxis(
                    y_range_name='NumIncidents',
                    axis_label='Number of Incidents',
                    axis_label_text_font_size='12pt',
                    axis_label_text_color='firebrick',
                    major_label_text_font_size='10pt',
                ),
                'right',
            )

            p1.line(
                total_num_incidents.index,
                total_num_incidents.values,
                line_width=5,
                color='firebrick',
                alpha=0.75,
                y_range_name='NumIncidents',
                legend_label='Number of Incidents',
            )

            p1.legend.location = "top_left"
            p1.legend.click_policy = "hide"

            p2 = figure(
                plot_width=800,
                plot_height=400,
                x_axis_type='datetime',
                x_axis_label='Date',
                y_axis_label='Number of Incidents',
                toolbar_location="above",
                tools=tools,
                x_range=p1.x_range,
            )

            p2.min_border_left = 150

            p2.y_range.start = 0

            p2.yaxis.axis_label_text_font_size = '12pt'
            p2.yaxis.major_label_text_font_size = '10pt'

            p2.xaxis.axis_label_text_font_size = '12pt'
            p2.xaxis.major_label_text_font_size = '10pt'

            stacked_area_source = ColumnDataSource(
                data=dict(
                    x=median_response_time.index
                )
            )
            for pc in PRIORITY_CODES:
                stacked_area_source.add(
                    priority_groups[pc],
                    name=pc,
                )

            p2.varea_stack(
                PRIORITY_CODES,
                x='x',
                source=stacked_area_source,
                color=('#bf9f84', 'darkolivegreen', '#e7cb75'),
                alpha=0.75,
                legend_label=[f"Priority {pc}" for pc in PRIORITY_CODES],
            )

            p2.legend.location = 'top_left'
            p2.legend.orientation = 'horizontal'
            p2.legend.spacing = 20

            tools = "pan,wheel_zoom,reset,save"
            map_options = GMapOptions(
                lat=cntr_lat,
                lng=cntr_lng,
                map_type="roadmap",
                zoom=14
            )

            p3 = gmap(
                GMAP_API_KEY,
                map_options,
                width=420,
                height=400,
                tools=tools,
                toolbar_location='above'
            )

            p3.yaxis.visible=False
            p3.xaxis.visible=False
            p3.min_border_left = 50

            lng_coords, lat_coords = [], []
            for pg in list(tract_geometry.geoms):
                c = pg.exterior.coords.xy
                lng_coords.append(list(c[0]))
                lat_coords.append(list(c[1]))

            source = ColumnDataSource(
                data=dict(
                    x=lng_coords,
                    y=lat_coords,
                )
            )

            p3.patches(
                'x', 'y',
                source=source,
                fill_color='darkslateblue',
                fill_alpha=0.5,
                line_color="black",
                line_width=1,
            )

            p = layout([[p3, p2], [p1]], spacing=50)

            save(p)

            script, div = components(p)

            with open(
                scripts_output_dir + f"stats_script_tract{tr}.js", 'w'
            ) as f:
                f.write(script)

            with open(
                div_output_dir + f"stats_div_tract{tr}.html", 'w'
            ) as f:
                f.write(div)

        return None
