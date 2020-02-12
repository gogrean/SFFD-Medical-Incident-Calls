class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class AddressError(Error):
    """Exception raised when an address cannot be geocoded."""

    def __init__(self, address, city, state):
        self.message = f"Unable to geocode the following address: {address}, {city} {state}."

    def __str__(self):
        return str(self.message)
