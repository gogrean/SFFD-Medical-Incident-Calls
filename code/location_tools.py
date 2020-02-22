from geopy.geocoders import Nominatim
import geocoder
from shapely.geometry import Point

from code.tract_tools import get_updated_tract_data
from code.exceptions import AddressError


def decode_address(address):
    """Geocode address."""
    geolocator = Nominatim(user_agent="my_fd_app")

    return geolocator.geocode(address, timeout=180)


def find_me():
    """Get geographical coordinates, city, and state based on user IP."""
    myloc = geocoder.ip('me')
    myloc_properties = myloc.geojson['features'][0]['properties']
    return {
        'city': myloc_properties['city'],
        'state': myloc_properties['state'],
    }


def add_city_state(address, city, state):
    """Return full address from street address, city, and state."""
    return address + f", {city} {state}"


def get_new_incident_address(street_address):
    """Return the address of a medical incident.

    Take in the street address of a medical incident as entered by the
    dispatcher, and combine it with the city and state of the dispatcher to
    get the full address of the incident.

    Warning: The assumption is that the dispatcher is in the same city as the
    one in which the incident happens, which should generally be true. The
    advantage of doing this is that the dispacher saves times by not having to
    enter the same city and state over and over again."""
    dispatch_loc = find_me()

    return {
        'address': add_city_state(
            street_address,
            dispatch_loc['city'],
            dispatch_loc['state'],
        ),
        'city': dispatch_loc['city'],
        'state': dispatch_loc['state'],
    }


def get_new_incident_coords(street_address):
    """Return the coordinates of a medical incident using its street address.

    See the warning in `get_new_incident_address` about assumptions made.
    """
    address = get_new_incident_address(street_address)
    lct = decode_address(address['address'])
    if lct:
        return (
            lct.longitude,
            lct.latitude,
            address['city'],
            address['state'],
        )
    return (None, None, address['city'], address['state'])


def get_new_incident_tract(lng, lat):
    """Return the tract corresponding to a given (longitude, latitude)."""
    # TODO: The Census file should not be hardcoded in here...
    tr = get_updated_tract_data(tracts_filename='Census_2010_Tracts.csv')
    lct = Point(lng, lat)
    for idx in range(len(tr.df)):
        if lct.within(tr.df.loc[idx]['Polygon']):
            return tr.df.loc[idx]['GEOID10']




def get_coords_from_address(street_address, city=None, state=None):
    """Return a geocoded location.

    Hacky way of deciphering an address and converting it to a GeoPy location
    with longitude and latitude attributes."""

    full_address = street_address
    if city and state:
        full_address = add_city_state(street_address, city, state)

    location = decode_address(full_address)
    if location:
        return location

    # if address not found on the first try
    for street_type in ['Street', 'Avenue', 'Road', 'Court', 'Way']:
        if city and state:
            full_address = add_city_state(
                f"{street_address} {street_type}",
                city,
                state
            )
        else:
            full_address = street_address.split(",", 1)[0] + \
                           f" {street_type}, " + street_address.split(",", 1)[1]

        location = decode_address(full_address)
        if location:
            return location

    # if all else fails... :-(
    raise AddressError(street_address, city, state)
