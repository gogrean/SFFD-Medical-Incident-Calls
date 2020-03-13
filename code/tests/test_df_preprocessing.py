import unittest
import datetime as dt

import pandas as pd

from code import utils


class TestModelFeatures(unittest.TestCase):
    """Test that features required by the ML model are created correctly."""

    def setUp(self):
        """Initialize a test dataframe."""

        col_name = 'Received DtTm'
        self.year, self.month, self.day = (
            '2018', '11', '05'
        )
        self.hour, self.minutes, self.seconds = (
            '00', '00', '00'
        )

        print(f'{self.year}-{self.month}-{self.day} {self.hour}:{self.minutes}:{self.seconds}')

        df_dict = {
            col_name: dt.datetime.strptime(
                f'{self.year}-{self.month}-{self.day} {self.hour}:{self.minutes}:{self.seconds}',
                '%Y-%m-%d %H:%M:%S'
            )
        }

        self.df = pd.DataFrame(
            pd.Series(
                df_dict[col_name],
                index=[0],
                name=col_name,
            )
        )

    def test_set_time_features(self):
        """Test that the time features are set correctly."""
        df_processed = utils.set_time_features(
            self.df,
            flag_weekends=True,
            flag_holidays=True,
            country='US',
            prov=None,
            state='CA',
        )

        self.assertEqual(
            set(
                df_processed.columns
            ),
            set(
                [
                    'Year',
                    'Day_of_Year_sin',
                    'Day_of_Year_cos',
                    'Day_of_Week_sin',
                    'Day_of_Week_cos',
                    'Hour_sin',
                    'Hour_cos',
                    'is_weekend',
                    'is_holiday',
                ]
            )
        )

        self.assertEqual(
            df_processed['Year'].values[0],
            int(self.year)
        )
        self.assertEqual(
            df_processed['Hour_sin'].values[0],
            0
        )
        self.assertEqual(
            df_processed['Hour_cos'].values[0],
            1
        )
        self.assertEqual(
            df_processed['is_weekend'].values[0],
            False
        )
        self.assertEqual(
            df_processed['is_holiday'].values[0],
            False
        )



if __name__ == '__main__':
    unittest.main()
