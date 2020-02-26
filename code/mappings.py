# A bunch of constants used throughout the code...


WEEKEND_DAYS = [5, 6]


AMBULANCE_UNITS = ['MEDIC', 'PRIVATE']


PRIORITY_CODES = [
    '3',
    '2',
    'E',
]

TRIG_PARAMS = {
    'hour': 24,
    'day_of_week': 7,
    'day_of_year': 366,
}

FEATURE_COLS = [
    'Tract',
    'Year',
    'Day_of_Year_sin',
    'Day_of_Year_cos',
    'Day_of_Week_sin',
    'Day_of_Week_cos',
    'Hour_sin',
    'Hour_cos',
    'is_weekend',
    'is_holiday',
    'Latitude',
    'Longitude',
    'Original Priority_2',
    'Original Priority_3',
    'Original Priority_E',
    'Unit Type_MEDIC',
    'Unit Type_PRIVATE',
]


NON_FEATURE_COLS = [
    'Call Number',
    'Unit ID',
    'Incident Number',
    'Call Type',
    'Call Date',
    'Watch Date',
    'Entry DtTm',
    'Dispatch DtTm',
    'Response DtTm',
    'Transport DtTm',
    'Hospital DtTm',
    'Call Final Disposition',
    'Available DtTm',
    'Address',
    'City',
    'Zipcode of Incident',
    'Battalion',
    'Station Area',
    'Box',
    'Priority',
    'Final Priority',
    'ALS Unit',
    'Call Type Group',
    'Number of Alarms',
    'Unit sequence in call dispatch',
    'Fire Prevention District',
    'Supervisor District',
    'Neighborhooods - Analysis Boundaries',
    'Location',
    'RowID'
]


COUNTIES = {
    'CA':
        {'San Francisco': 'San Francisco',
         'Oakland': 'Alameda',
         'Alameda': 'Alameda',
         'Menlo Park': 'San Mateo',
        }
}

# Source: https://gist.github.com/rogerallen/1583593
US_STATE_ABBR = {
    'Alabama': 'AL',
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'District of Columbia': 'DC',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Northern Mariana Islands':'MP',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Palau': 'PW',
    'Pennsylvania': 'PA',
    'Puerto Rico': 'PR',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virgin Islands': 'VI',
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY',
}


DEFAULT_PARAM_DISTR_RFR = dict(
    n_estimators=[50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300],
    max_features=['log2', 'auto'],
    min_samples_split=[50, 100, 200, 400, 800, 1600]
)
