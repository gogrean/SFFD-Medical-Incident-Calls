import unittest

from code import utils


class TestBokehPlots(unittest.TestCase):
    """Test the function `get_fig_components` in the `utils` module."""

    def setUp(self):
        self.div_filepath_success = 'test_data/test_div.html'
        self.js_filepath_success = 'test_data/test_js.js'
        self.div_filepath_fail = ''
        self.js_filepath_fail = ''

    def test_get_fig_components(self):
        div_success, js_success = utils.get_fig_components(
            div_filepath=self.div_filepath_success,
            js_filepath=self.js_filepath_success,
        )

        self.assertEqual(div_success.strip(), '<div></div>')
        self.assertEqual(js_success.strip(), '<script></script>')

        with self.assertRaises(FileNotFoundError):
            _, _ = utils.get_fig_components(
                div_filepath=self.div_filepath_fail,
                js_filepath=self.js_filepath_fail,
            )

if __name__ == '__main__':
    unittest.main()
