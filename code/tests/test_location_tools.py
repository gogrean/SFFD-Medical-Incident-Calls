import unittest

from code import location_tools
from code import exceptions


class TestLocationTools(unittest.TestCase):
    """Test that the function `get_coords_from_address` correctly decodes
    known addresses or fails as expected.

    The following addresses are tested:
        (1) 683 Sutter St, San Francisco, CA
        (2) 15 Embarcadero, San Francisco, CA
        (3) 683 Sutter St, with city=San Francisco and state=CA
        (4) blah blah blah, San Francisco, CA
        (5) blab blob"""

    def setUp(self):
        existing_street_address1 = "683 Sutter St"
        existing_street_address2 = "15 Embarcadero"
        madeup_street_address1 = "blah blah blah"
        madeup_address2 = "blab blob"

        self.city = "San Francisco"
        self.state = "CA"

        self.existing_street_address1 = existing_street_address1
        self.madeup_address2 = madeup_address2

        self.existing_address1 = " ".join(
            [
                existing_street_address1,
                self.city,
                self.state,
            ]
        )

        self.existing_address2 = " ".join(
            [
                existing_street_address2,
                self.city,
                self.state,
            ]
        )

        self.madeup_address1 = " ".join(
            [
                madeup_street_address1,
                self.city,
                self.state,
            ]
        )

    def test_get_coords_from_address(self):

        # test "683 Sutter St, San Francisco, CA"
        self.assertIsInstance(
            location_tools.get_coords_from_address(
                self.existing_address1
            ).latitude, float
        )

        # test "683 Sutter St, San Francisco, CA"
        self.assertIsInstance(
            location_tools.get_coords_from_address(
                self.existing_address1
            ).longitude, float
        )

        # test "15 Embarcadero, San Francisco, CA"
        self.assertIsInstance(
            location_tools.get_coords_from_address(
                self.existing_address2
            ).latitude, float
        )

        # test "15 Embarcadero, San Francisco, CA"
        self.assertIsInstance(
            location_tools.get_coords_from_address(
                self.existing_address2
            ).longitude, float
        )

        # test "683 Sutter St" with city and state attributes
        self.assertIsInstance(
            location_tools.get_coords_from_address(
                self.existing_street_address1,
                city=self.city,
                state=self.state,
            ).latitude, float
        )

        # test "683 Sutter St" with city and state attributes
        self.assertIsInstance(
            location_tools.get_coords_from_address(
                self.existing_address1,
                city=self.city,
                state=self.state,
            ).longitude, float
        )

        # test "blah blah blah, San Francisco, CA"
        with self.assertRaises(exceptions.AddressError):
            location_tools.get_coords_from_address(
                self.madeup_address1
            )

        # test "blab blob"
        with self.assertRaises(exceptions.AddressError):
            location_tools.get_coords_from_address(
                self.madeup_address2
            )


if __name__ == '__main__':
    unittest.main()
