from geopy.geocoders import Nominatim
import geocoder

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
        'latitude': myloc_properties['lat'],
        'longitude': myloc_properties['lng'],
    }

def add_city_state(address, city, state):
    return address + f", {city} {state}"


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
