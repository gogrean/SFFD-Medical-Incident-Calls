from flask_sqlalchemy import SQLAlchemy
from geoalchemy2.types import Geometry

from utils import get_secret_key

import sys

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
                f"Fire Station Address = {self.station_address} \n")


class SFHospital(db.Model):
    """Model the table of SF hospitals where ambulances transport patients."""

    __tablename__ = 'hospitals'

    hospital_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hospital_name = db.Column(db.String(100), nullable=False)
    hospital_address = db.Column(db.String(100), nullable=False)
    hospital_coords = db.Column(Geometry(geometry_type='POINT'), nullable=False)

    def __repr__(self):
        return (f"Hospital Name = {self.hospital_name} \n"
                f"Hospital Address = {self.hospital_address} \n")


class MedicalCall(db.Model):
    """Model the table of emergency calls requiring an ambulance."""

    __tablename__ = 'medical_calls'

    call_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    als_unit = db.Column(db.Boolean, nullable=False)
    coords = db.Column(Geometry(geometry_type='POINT'), nullable=False)
    zipcode = db.Column(db.String(10))
    call_type_group = db.Column(db.String(50))
    neighborhood = db.Column(db.String(50), nullable=False)

    vars = ['call_number', 'incident_number',
            'number_alarms', 'unit_seq_dispatch']
    var_dict = dict([(var, db.Column(db.Integer, nullable=False))
                     for var in vars])

    vars = ['call_date', 'watch_date']
    var_dict.update([(var, db.Column(db.Date, nullable=False)) for var in vars])

    vars = ['received_dttm', 'entry_dttm', 'dispatch_dttm']
    var_dict.update([(var, db.Column(db.DateTime, nullable=False))
                     for var in vars])

    vars = ['response_dttm', 'onscene_dttm', 'transport_dttm',
            'hospital_dttm', 'available_dttm']
    var_dict.update([(var, db.Column(db.DateTime)) for var in vars])

    vars = ['call_type', 'rowid', 'unit_type']
    var_dict.update([(var, db.Column(db.String(25), nullable=False))
                     for var in vars])

    vars = ['address', 'location', 'call_final_disposition']
    var_dict.update([(var, db.Column(db.String(100), nullable=False))
                     for var in vars])

    vars = ['city', 'tract', 'box']
    var_dict.update([(var, db.Column(db.String(25))) for var in vars])

    vars = ['battalion', 'final_priority',
            'fire_district', 'supervisor_district']
    var_dict.update([(var, db.Column(db.String(5), nullable=False))
                     for var in vars])

    vars = ['station_area', 'original_priority', 'priority']
    var_dict.update([(var, db.Column(db.String(5))) for var in vars])

    locals().update(var_dict)

    def __repr__(self):
        return (f"Received DtTm: {self.received_dttm} \n"
                f"On Scene DtTm: {self.onscene_dttm} \n"
                f"Location: {self.location} \n"
                f"Original Priority: {self.original_priority} \n"
                f"Unit Type: {self.unit_type} \n")


class TractGeometry(db.Model):
    """Model the table of tracts from the US Census."""

    __tablename__ = 'tract_geom'

    geoid10 = db.Column(db.String(15), primary_key=True)
    aland10 = db.Column(db.Integer, nullable=False)
    awater10 = db.Column(db.Integer, nullable=False)
    the_geom = db.Column(Geometry(geometry_type='MULTIPOLYGON'))

    def __repr__(self):
        return (f"GeoID10: {self.geoid10} \n"
                f"Land Area: {self.aland10} sq meters \n"
                f"Water Area: {self.awater10} sq meters \n")


# class TractIncome(db.Model):
#     """Model the table of income statistics by tract."""
#
#     __tablename__ = 'income'
#
#     pass
#
#
# class TractDemo(db.Model):
#     """Model the table with demographic info by tract."""
#
#     __tablename__ = 'demographics'
#
#     pass


def connect_to_db(app):
    # reads the database name from a YAML file
    DB_NAME = get_secret_key('DB_NAME')

    DB_URI = f"postgresql:///{DB_NAME}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
    db.app = app
    db.init_app(app)
