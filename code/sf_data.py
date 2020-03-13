import urllib

from bs4 import BeautifulSoup
import pandas as pd

from code.location_tools import get_coords_from_address
from code.tract_tools import get_updated_tract_data, build_multipolygon
from code.key_utils import get_secret_key


def get_medical_calls(filename='Med_Calls_with_Tracts.pkl'):
    """Read the pickled dataframe of SF medical calls."""

    DATA_DIR = get_secret_key('DATA_DIR')

    return pd.read_pickle(DATA_DIR + filename)


def get_tract_geom(update_tract_geom=True,
                   tracts_filename='Census_2010_Tracts.csv'):
    """Get the tract geometry.

    The tract geometry information can be read directly from a CSV file if
    `update_tract_geom=False`, or after intersecting the tracts with a
    county shape file to create more accurate boundaries and change the
    geometry of the polygons defining the tracts."""

    tract_geom = []
    if update_tract_geom:
        tracts = get_updated_tract_data(tracts_filename)
        for idx in tracts.df.index:
            geoid10 = tracts.df.at[idx, 'GEOID10']
            # converting these from type 'np.int64', which returns the
            # following error when trying to insert into the database:
            #
            # psycopg2.ProgrammingError: can't adapt type 'numpy.int64'
            #
            # to type 'int', which somehow works...
            aland10 = int(tracts.df.at[idx, 'ALAND10'])
            awater10 = int(tracts.df.at[idx, 'AWATER10'])
            multipolygon_constructor = build_multipolygon(tracts, geoid10)

            tract_geom.append((geoid10, aland10, awater10,
                               multipolygon_constructor))

        return tract_geom
    else:
        # TODO: Implement reading the tract data as is from a CSV file.
        raise Warning("Sorry, this is not implemented yet...")



def get_hospitals():
    """Get list of hospitals in SF where ambulances transport patients."""

    DATA_DIR = get_secret_key('DATA_DIR')
    sf_hospitals_fp = DATA_DIR + "sf_hospitals.txt"

    hospitals = []

    with open(sf_hospitals_fp, 'r') as f:
        for hospital in f.readlines():
            hospital_data = hospital.split("|")
            hospital_name = hospital_data[0].strip()
            hospital_address = hospital_data[1].strip()
            lct = get_coords_from_address(hospital_address)
            hospitals.append((hospital_name,
                              hospital_address,
                              lct.longitude, lct.latitude))

    return hospitals


def get_fire_stations():
    """Get a list of San Francisco fire stations.

    The function scrapes the website of the SF Fire Department to get a list
    of fire stations. It then geocodes the station addresses into
    (longitude, latitude) and returns a list of tuples containing the name
    of the fire station, its address, and its geographical coordinates."""

    sffd_url = 'https://sf-fire.org/fire-station-locations'

    with urllib.request.urlopen(sffd_url) as page:
        html = BeautifulSoup(page.read(), features='html.parser')

    fire_station_html_table = html.find('div', {'class': 'view-opensf-layout'})

    fire_stations = []

    for row in fire_station_html_table.find_all('tr'):
        station_name_html, station_address_html = row.find_all('td')

        # Some station names appear as "Station 16 CURRENTLY BEING RENOVATED",
        # so everything but the first two words are being removed. In this example,
        # that would leave "Station 16".
        station_name = " ".join(station_name_html.text.strip().split()[:2])

        # All addresses have a cross street, e.g. "935 Folsom at 5th Street".
        # Everything starting at " at " is removed, so that in the example above
        # that would leave "935 Folsom"
        station_address_with_crossstreet = station_address_html.text.strip().replace(u'\xa0', u' ')
        cross_street_start_index = station_address_with_crossstreet.find(' at ')
        station_address = station_address_with_crossstreet[:cross_street_start_index]

        # There's one weird address to handle in the SF fire station addresses:
        # "Pier 22½, The Embarcadero". This address gets geocoded if "The Embarcadero"
        # is removed, so that's what is being done. Hacky... :-/
        if "," in station_address:
            station_address = station_address.replace(u'22½', u'22 1/2')
            comma_index = station_address.find(',')
            station_address = station_address[:comma_index]

        if station_address:
            lct = get_coords_from_address(station_address, 'San Francisco', 'CA')
            fire_stations.append((station_name,
                                  f"{station_address}, San Francisco, CA",
                                  lct.longitude, lct.latitude))

    return fire_stations
