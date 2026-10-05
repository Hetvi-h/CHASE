from sqlalchemy import Column, Integer, String, Float, Boolean, Date, Time, BigInteger, text
from sqlalchemy.orm import declarative_base
from geoalchemy2 import Geometry

Base = declarative_base()

class CrimeMaster(Base):
    __tablename__ = 'crimes_master'
    report_number = Column('Report Number', BigInteger, primary_key=True)
    date_reported = Column('Date Reported', Date)
    date_of_occurrence = Column('Date of Occurrence', Date)
    time_of_occurrence = Column('Time of Occurrence', Time)
    city = Column('City', String)
    crime_code = Column('Crime Code', BigInteger)
    crime_description = Column('Crime Description', String)
    victim_age = Column('Victim Age', Integer)
    victim_gender = Column('Victim Gender', String)
    weapon_used = Column('Weapon Used', String)
    crime_domain = Column('Crime Domain', String)
    police_deployed = Column('Police Deployed', Integer)
    case_closed = Column('Case Closed', String)
    date_case_closed = Column('Date Case Closed', Date)
    state = Column('State', String)
    city_latitude = Column('City_Latitude', Float)
    city_longitude = Column('City_Longitude', Float)
    is_synthetic_row = Column('Is_Synthetic_Row', Boolean)
    zone_id = Column('Zone_ID', String)
    latitude = Column('Latitude', Float)
    longitude = Column('Longitude', Float)
    geom = Column(Geometry(geometry_type='POINT', srid=4326))

class ZoneReference(Base):
    __tablename__ = 'zone_reference'
    zone_id = Column('Zone_ID', String, primary_key=True)
    city = Column('City', String)
    zone_latitude = Column('Zone_Latitude', Float)
    zone_longitude = Column('Zone_Longitude', Float)
    zone_weight = Column('Zone_Weight', Float)
    is_primary_center = Column('Is_Primary_Center', Boolean)
    zone_radius_km = Column('Zone_Radius_Km', Float)
    geom = Column(Geometry(geometry_type='POINT', srid=4326))

class SurveySynthetic(Base):
    __tablename__ = 'survey_synthetic'
    survey_id = Column('survey_id', BigInteger, primary_key=True)
    zone_id = Column('Zone_ID', String)
    respondent_age_bracket = Column('respondent_age_bracket', String)
    respondent_gender = Column('respondent_gender', String)
    time_of_day_band = Column('time_of_day_band', String)
    safety_rating = Column('safety_rating', Integer)
    primary_concern = Column('primary_concern', String)
    visits_after_dark_frequency = Column('visits_after_dark_frequency', String)
    suggested_improvement = Column('suggested_improvement', String)
    response_date = Column('response_date', Date)

class NCRBCityTotals(Base):
    __tablename__ = 'ncrb_city_totals_2023'
    city = Column('City', String, primary_key=True)
    total_ipc_sll = Column('NCRB_2023_Total_IPC_SLL', BigInteger)

class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(String, primary_key=True)
    email = Column(String)
    full_name = Column(String)
    role = Column(String, default='viewer')
    created_at = Column(String)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    user_email = Column(String)
    action = Column(String)
    details = Column(String) # JSON string
    ip_address = Column(String)
    created_at = Column(String)
