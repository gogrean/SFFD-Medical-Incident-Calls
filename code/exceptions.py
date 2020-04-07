class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class AddressError(Error):
    """Exception raised when an address cannot be geocoded."""

    def __init__(self, address, city=None, state=None):
        error_message = "Unable to geocode the following address:"
        if city and state:
            self.message = f"{error_message} {address}, {city}, {state}."
        elif city:
            self.message = f"{error_message} {address}, {city}."
        elif state:
            self.message = f"{error_message} {address}, {state}."
        else:
            self.message = f"{error_message} {address}."

    def __str__(self):
        return str(self.message)
