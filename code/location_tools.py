from geopy.geocoders import Nominatim

from custom_exceptions import AddressError


def decode_address(address):
    geolocator = Nominatim(user_agent="my_fd_app")
    return geolocator.geocode(address)

def get_coords_from_address(street_address, city, state):
    location = decode_address(f"{street_address}, {city} {state}")
    if location:
        return location

    # if address not found on the first try
    for street_type in ['Avenue', 'Street', 'Road', 'Court', 'Way']:
        location = decode_address(f"{street_address} {street_type}, {city} {state}")
        if location:
            return location

    # if all else fails
    raise AddressError(street_address, city, state)
