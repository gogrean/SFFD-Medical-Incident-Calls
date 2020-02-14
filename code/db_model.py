from flask_sqlalchemy import SQLAlchemy
from geoalchemy2.types import Geometry

from utils import get_secret_key


db = SQLAlchemy()

class SFFDFireStation(db.Model):
    """Model the fire station table in the database."""

    __tablename__ = 'fire_stations'

    station_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    station_name = db.Column(db.String(50), nullable=False)
    station_address = db.Column(db.String(100), nullable=False)
    station_coords = db.Column(Geometry(geometry_type='POINT'),
                               nullable=False)

    def __repr__(self):
        return (f"Fire Station Name = {self.station_name} \n"
                f"Fire Station Address = {self.station_address} \n\n")

class SFHospital(db.Model):
    """Model the table of SF hospitals where ambulances transport patients."""

    __tablename__ = 'hospitals'

    hospital_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hospital_name = db.Column(db.String(100), nullable=False)
    hospital_address = db.Column(db.String(100), nullable=False)
    hospital_coords = db.Column(Geometry(geometry_type='POINT'),
                                nullable=False)

    def __repr__(self):
        return (f"Hospital Name = {self.hospital_name} \n"
                f"Hospital Address = {self.hospital_address} \n\n")


def connect_to_db(app):
    # reads the database name from a YAML file
    DB_NAME = get_secret_key('DB_NAME')

    DB_URI = f"postgresql:///{DB_NAME}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
    db.app = app
    db.init_app(app)
