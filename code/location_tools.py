def get_coords_from_address(address):
    """Convert address to geographical location.
        
    The function returns a `location` parameter that has
    `.latitude` and `.longitude` attributes to get the
    geographical coordinates."""

    from geopy.geocoders import Nominatim
    
    geolocator = Nominatim(user_agent="my_fd_app")
    location = geolocator.geocode(address)
    
    return location

