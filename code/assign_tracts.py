import re

import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon

DATA_DIR = '/Users/gogrean/Documents/data_projects/Fire_Department_Calls/data/'

class Tracts:
    """Get the US Census tract data.

    The class loads the tract data and converts the boundaries of each
    tract into a `shapely` polygon."""

    def __init__(self, tracts_filename='Census_2010_Tracts.csv'):
        """
        Read the US Census tract data.
        """
        tracts_df = pd.read_csv(DATA_DIR + tracts_filename,
                                usecols=['GEOID10', 'the_geom', 'ALAND10',
                                         'AWATER10', 'NAMELSAD10'])
        tracts_df['GEOID10'] = tracts_df['GEOID10'].astype('str')
        self.df = tracts_df

    def _convert_boundary_to_shapely_polygon(self):
        """
        Convert boundary coordinates to `shapely` POLYGON.

        In the tract dataframe, create a column the defines the boundary of
        each tract in a 'shapely' POLYGON format.

        The tract dataframe must have a 'the_geom' column containing the
        coordinates of the polygon boundaries.
        """
        start, end = 'MULTIPOLYGON (((', ')))'

        for i, tract in enumerate(self.df['the_geom']):
            tract_poly_str = tract[len(start):-len(end)]
            tract_poly_arr = [[float(x.split()[0]), float(x.split()[1])]
                                        for x in tract_poly_str.split(',')]
            tract_poly = Polygon(tract_poly_arr)
            self.df.loc[i, 'Polygon'] = tract_poly

        self.df.drop(labels='the_geom', axis=1, inplace=True)


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
        tracts._convert_boundary_to_shapely_polygon()
        return tracts

    @staticmethod
    def _find_tract(tracts, location):
        """Find the tract that each (lon, lat) pair is in."""
        for idx, polygon in tracts.df['Polygon'].items():
            if location.within(polygon):
                tract = tracts.df.at[idx, 'GEOID10']
                return tract
        return np.nan

    def assign_tracts_to_calls(self, tracts_filename='Census_2010_Tracts.csv'):
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
