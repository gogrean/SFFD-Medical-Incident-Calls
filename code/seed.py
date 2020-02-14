from contextlib import contextmanager

from sqlalchemy_utils import drop_database, create_database, database_exists
from sqlalchemy.orm import sessionmaker

from db_model import connect_to_db, db
from db_model import SFFDFireStation, SFHospital
from app import app
from utils import get_secret_key
from sf_data import get_fire_stations, get_hospitals


def load_fire_station_table():
    """Load the fire stations into the database."""
    SFFDFireStation.query.delete()

    stations = get_fire_stations()
    db_stations = []
    for station in stations:
        db_station = SFFDFireStation(
                                     station_name=station[0],
                                     station_address=station[1],
                                     station_coords=f"POINT({station[2]} {station[3]})"
                                    )
        db_stations.append(db_station)
    db.session.add_all(db_stations)
    db.session.commit()


def load_hospital_table():
    """Load the hospitals into the database."""
    SFHospital.query.delete()

    hospitals = get_hospitals()
    db_hospitals = []
    for hospital in hospitals:
        db_hospital = SFHospital(
                                 hospital_name=hospital[0],
                                 hospital_address=hospital[1],
                                 hospital_coords=f"POINT({hospital[2]} {hospital[3]})"
                                )
        db_hospitals.append(db_hospital)
    db.session.add_all(db_hospitals)
    db.session.commit()


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

    load_fire_station_table()
    load_hospital_table()
