import re

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon

DATA_DIR = '/Users/gogrean/Documents/data_projects/Fire_Department_Calls/data/'


class CountyShape:
    """Get county boundaries.

    The tracts near the border of the counties in the US Census are very
    rough, especially if the county borders water. To nicely plot the tracts,
    a `shp` file with more precise boundary definitions is intersected with
    the tract polygons defined in the US Census. The tract boundaries are
    adjusted to the border coordinates in the `shp` file for tract boundary
    coordinates found to be outside of the border defined in the `shp` file."""

    def __init__(self, county):
        # Read a `shp` file with county edge coordinates.
        shp_fp = "Bay_Area_County_Boundaries/ark28722-s7hs4j-shapefile/s7hs4j.shp"
        shp = gpd.read_file(DATA_DIR + shp_fp, encoding='UTF-8')
        # Filter on county name.
        if any(shp['COUNTY'] == county):
            self.boundary = shp[shp['COUNTY'] == county]['geometry']
        else:
            raise ValueError('Shape file not found!')


class Tracts:
    """Get the US Census tract data.

    The class loads the tract data and converts the boundaries of each
    tract into a `shapely` polygon."""

    def __init__(self,
                 county='San Francisco',
                 tracts_filename='Census_2010_Tracts.csv'):
        """
        Read the US Census tract data.
        """
        tracts_df = pd.read_csv(DATA_DIR + tracts_filename,
                                usecols=['GEOID10', 'the_geom', 'ALAND10',
                                         'AWATER10', 'NAMELSAD10'])
        tracts_df['GEOID10'] = tracts_df['GEOID10'].astype('str')
        self.df = tracts_df
        self.county = county
        self.longitude, self.latitude = [], []
        self.tract_names = []

    def _convert_boundary_to_shapely_polygon(self):
        """Convert boundary coordinates to `shapely` POLYGON.

        In the tract dataframe, create a column the defines the boundary of
        each tract in a 'shapely' POLYGON format.

        The tract dataframe must have a 'the_geom' column containing the
        coordinates of the polygon boundaries."""
        start, end = 'MULTIPOLYGON (((', ')))'

        for i, tract in enumerate(self.df['the_geom']):
            tract_poly_str = tract[len(start):-len(end)]
            tract_poly_arr = [[float(x.split()[0]), float(x.split()[1])]
                                        for x in tract_poly_str.split(',')]
            tract_poly = Polygon(tract_poly_arr)
            self.df.loc[i, 'Polygon'] = tract_poly

        self.df.drop(labels='the_geom', axis=1, inplace=True)

    def get_boundaries(self):
        """Intersect the county boundary with the tract polygons.

        The tract polygons have rough edges and do not presisely follow the
        contours of the county's boundary. Intersecting the tracts with the
        county shape ensures a correct mapping of each tract's land area.
        """
        self._convert_boundary_to_shapely_polygon()
        county = CountyShape(self.county)
        # TODO: Would it make more sense to index this by tract id?
        for i in self.df.index:
            tract_id = self.df.at[i, 'GEOID10']
            # If the tract has any land area...
            if self.df.at[i, 'ALAND10']:
                # This is the land area of (most of) San Francisco County.
                # Also included in SF County are a few islands around the
                # continental part? Those are mapped in sf.values[0][1:19].
                # I will ignore those areas for now, hence the use of
                # county.boundary.values[0][0].
                # TODO: Handle multiple boundary polygons.
                land_poly = self.df.at[i, 'Polygon'].intersection(
                            county.boundary.values[0][0])
                try:
                    tract_coords_xy = [(x, y)
                                       for x, y in land_poly.exterior.coords]
                # AttributeError is thrown if the intersection between
                # self.df.at[i, 'Polygon'] and county.boundary.values[0][0]
                # results in unconnected polygons. The individual polygons
                # are then handled separately, making sure that the same tract
                # number is assigned to all of them.
                except AttributeError:
                    multi_land_polys = list(land_poly)
                    n_polys = len(multi_land_polys)
                    for p in multi_land_polys:
                        tract_coords_xy = [(x, y) for x, y in p.exterior.coords]
                        self.longitude.append(
                                                [x for x, _ in tract_coords_xy])
                        self.latitude.append(
                                                [y for _, y in tract_coords_xy])
                else:
                # This else is here just to avoid having all this code under
                # the `try` statement.
                    n_polys = 1
                    self.longitude.append([x for x, _ in tract_coords_xy])
                    self.latitude.append([y for _, y in tract_coords_xy])
                finally:
                    self.tract_names.extend([tract_id]*n_polys)


class MedicalIncidents():
    """Get the medical incidents database.

    Read the fire department incident database, filter by medical incidents,
    assign a tract to each incident."""

    def __init__(self, fd_call_filename):
        """Load medical incidents in fire department call dataset."""
        all_call_df = pd.read_csv(DATA_DIR + fd_call_filename,
                                  header=0,
                                  parse_dates=True)

        def _parse_dates():
            """Parse date columns to `datetime` format."""
            for col in ['Call Date', 'Watch Date']:
                all_call_df[col] = pd.to_datetime(all_call_df[col],
                                                  format='%m/%d/%Y')
            for col in ['Received DtTm', 'Entry DtTm', 'Dispatch DtTm',
                        'Response DtTm', 'On Scene DtTm', 'Transport DtTm',
                        'Hospital DtTm', 'Available DtTm']:
                all_call_df[col] = pd.to_datetime(all_call_df[col],
                                                  format='%m/%d/%Y %I:%M:%S %p')

        def _get_medical_incidents():
            """
            Filter call dataset to only include medical incidents.

            TODO: Take this out of this function and put it in the init. It
            looks stupid here and it's unnecessary.
            """
            df = all_call_df[all_call_df['Call Type'] =='Medical Incident']
            return df

        _parse_dates()
        self.df = _get_medical_incidents()

    def update_cached_df(self, pickled_df_filename='Med_Calls_with_Tracts.pkl'):
        """Save the pickled dataframe."""
        self.df.to_pickle(DATA_DIR + pickled_df_filename)

    def _convert_coords_to_shapely_point(self):
        """
        Convert (lon, lat) for each event to `shapely` POINT.

        For each event, store its coordinates in 'shapely' POINT format.
        This will make it easy to check whether an event is within a certain
        US Census tract, since the tract boundaries are saved as POLYGONs.
        """
        points = []
        for i, location in zip(self.df.index,
                               self.df['Location']):
            try:
                lat = float(re.search(r'\((.*?)\,', location).group(1))
                lon = float(re.search(r'\, (.*?)\)', location).group(1))
            except TypeError:
                # If any of the events is missing the location in the original,
                # dataset, leave the Coords value to np.nan and move on.
                lat, lon = np.nan, np.nan
            points.append(Point(lon, lat))
        self.df['Coords'] = points

    @staticmethod
    def _get_tract_data(tracts_filename):
        """Make Tracts() object, with the boundaries as `shapely` polygons."""
        tracts = Tracts(tracts_filename=tracts_filename)
        tracts.get_boundaries()
        return tracts

    @staticmethod
    def _find_tract(tracts, location):
        """Find the tract that each (lon, lat) pair is in."""
        for idx, polygon in tracts.df['Polygon'].items():
            if location.within(polygon):
                tract = tracts.df.at[idx, 'GEOID10']
                return tract
        return np.nan

    def assign_tracts_to_calls(self, tracts_filename='Census_2010_Tracts.csv',
                               update_cached_df=False,
                               pickled_df_filename='Med_Calls_with_Tracts.pkl'):
        """Assign tracts to each ambulance call.

        The tracts used come from the 2010 US Census. The ambulance call
        database has (lon, lat) locations for each of the events. This function
        uses the tract boundaries to assign a tract to each (lon, lat) location
        in the call database.
        """
        tracts = self._get_tract_data(tracts_filename)
        self._convert_coords_to_shapely_point()

        for idx, location in self.df['Coords'].items():
            self.df.at[idx, 'Tract'] = self._find_tract(tracts, location)

        # Save the pickled dataframe.
        if update_cached_df:
            self.update_cached_df(pickled_df_filename)
