from geopy.geocoders import Nominatim

from exceptions import AddressError


def decode_address(address):
    """Geocode address."""

    geolocator = Nominatim(user_agent="my_fd_app")
    return geolocator.geocode(address, timeout=180)


def get_coords_from_address(street_address, city=None, state=None):
    """Return a geocoded location.

    Hacky way of deciphering an address and converting it to a GeoPy location
    with longitude and latitude attributes."""

    def add_city_state(address):
        return address + f", {city} {state}"

    full_address = street_address
    if city and state:
        full_address = add_city_state(street_address)

    location = decode_address(full_address)
    if location:
        return location

    # if address not found on the first try
    for street_type in ['Street', 'Avenue', 'Road', 'Court', 'Way']:
        if city and state:
            full_address = add_city_state(f"{street_address} {street_type}")
        else:
            full_address = street_address.split(",", 1)[0] + \
                           f" {street_type}, " + street_address.split(",", 1)[1]

        location = decode_address(full_address)
        if location:
            return location

    # if all else fails
    raise AddressError(street_address, city, state)
