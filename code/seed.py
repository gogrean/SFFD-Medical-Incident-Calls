from contextlib import contextmanager

from sqlalchemy_utils import drop_database, \
                             create_database, \
                             database_exists
from sqlalchemy.orm import sessionmaker

from code.db_model import connect_to_db, \
                          db, \
                          SFFDFireStation, \
                          SFHospital, \
                          TractGeometry, \
                          MedicalCall
from code.flaskr import app
from code.key_utils import get_secret_key
from code.sf_data import get_fire_stations, \
                         get_hospitals, \
                         get_tract_geom, \
                         get_medical_calls


def load_fire_station_table():
    """Load the fire stations into the database."""
    SFFDFireStation.query.delete()

    stations = get_fire_stations()
    db_stations = []
    for station in stations:
        db_station = SFFDFireStation(
            station_name = station[0],
            station_address = station[1],
            coords = f"POINT({station[2]} {station[3]})"
        )
        db_stations.append(db_station)

    return db_stations


def load_hospital_table():
    """Load the hospitals into the database."""
    SFHospital.query.delete()

    hospitals = get_hospitals()
    db_hospitals = []
    for hospital in hospitals:
        db_hospital = SFHospital(
             hospital_name = hospital[0],
             hospital_address = hospital[1],
             coords = f"POINT({hospital[2]} {hospital[3]})"
        )
        db_hospitals.append(db_hospital)

    return db_hospitals


def load_tract_geom_table():
    """Load the tract geometry into the database."""
    TractGeometry.query.delete()

    tracts = get_tract_geom()
    db_tracts = []
    for tract in tracts:
        db_tract = TractGeometry(
                                 geoid10 = tract[0],
                                 aland10 = tract[1],
                                 awater10 = tract[2],
                                 the_geom = tract[3]
                                )
        db_tracts.append(db_tract)

    return db_tracts


def load_medical_call_table():
    """Load the table of medical calls into the database."""
    MedicalCall.query.delete()

    column_mapper = {'ALS Unit': 'als_unit', 'Coords': 'coords',
                     'Zipcode of Incident': 'zipcode',
                     'Call Type Group': 'call_type_group',
                     'Neighborhooods - Analysis Boundaries': 'neighborhood',
                     'Call Number': 'call_number',
                     'Incident Number': 'incident_number',
                     'Number of Alarms': 'number_alarms',
                     'Unit sequence in call dispatch': 'unit_seq_dispatch',
                     'Call Date': 'call_date', 'Watch Date': 'watch_date',
                     'Received DtTm': 'received_dttm',
                     'Entry DtTm': 'entry_dttm',
                     'Dispatch DtTm': 'dispatch_dttm',
                     'Response DtTm': 'response_dttm',
                     'On Scene DtTm': 'onscene_dttm',
                     'Transport DtTm': 'transport_dttm',
                     'Hospital DtTm': 'hospital_dttm',
                     'Available DtTm': 'available_dttm',
                     'Call Type': 'call_type', 'RowID': 'rowid',
                     'Call Final Disposition': 'call_final_disposition',
                     'Unit Type': 'unit_type',
                     'Address': 'address', 'Location': 'location',
                     'City': 'city', 'Tract': 'tract', 'Battalion': 'battalion',
                     'Final Priority': 'final_priority',
                     'Fire Prevention District': 'fire_district',
                     'Supervisor District': 'supervisor_district',
                     'Station Area': 'station_area', 'Box': 'box',
                     'Original Priority': 'original_priority',
                     'Priority': 'priority'}

    medical_calls = get_medical_calls()
    medical_calls.rename(columns=column_mapper, inplace=True)

    possible_NaT_cols = ['response_dttm', 'onscene_dttm', 'transport_dttm',
                         'hospital_dttm', 'available_dttm']
    for col in possible_NaT_cols:
        medical_calls[col] = medical_calls[col].astype(object).where(medical_calls[col].notnull(), None)

    medical_calls['coords'] = 'POINT' + medical_calls['location'].str.replace(',', '')

    return medical_calls



if __name__ == "__main__":
    connect_to_db(app)

    Session = sessionmaker(bind=db.engine)

    @contextmanager
    def session_scope():
        """Provide a transational scope around creating a postgis extension
        when the database is being created."""
        session = Session(bind=db.engine.connect())
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    DB_NAME = get_secret_key('DB_NAME')
    DB_URI = f"postgresql:///{DB_NAME}"

    if not database_exists(DB_URI):
        create_database(DB_URI)
        with session_scope() as session:
            session.execute("CREATE SCHEMA postgis;")
            session.execute("ALTER DATABASE medical_calls_db SET search_path=public, postgis, contrib;")
            session.execute("CREATE EXTENSION postgis SCHEMA postgis;")

    # Create the tables in the database.
    db.create_all()

    # load the medical call table
    with session_scope() as session:
        db_medical_calls = load_medical_call_table()
        session.bulk_insert_mappings(MedicalCall,
                                     db_medical_calls.to_dict(orient='records'))


    # load the tract geometry table
    with session_scope() as session:
        db_tract_geom = load_tract_geom_table()
        session.add_all(db_tract_geom)

    # load the hospital table
    with session_scope() as session:
        db_hospitals = load_hospital_table()
        session.add_all(db_hospitals)

    # load the fire station table
    with session_scope() as session:
        db_fire_stations = load_fire_station_table()
        session.add_all(db_fire_stations)
