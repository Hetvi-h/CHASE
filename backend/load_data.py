import pandas as pd
import os
from sqlalchemy import text
from database import engine
from models import Base

def load_data():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    datasets_dir = r"C:\PROJECTS\CHASE\datasets"
    
    print("Loading ncrb_city_totals_2023.csv...")
    ncrb = pd.read_csv(os.path.join(datasets_dir, "ncrb_city_totals_2023.csv"))
    ncrb.to_sql('ncrb_city_totals_2023', engine, if_exists='replace', index=False)
    
    print("Loading zone_reference.csv...")
    zones = pd.read_csv(os.path.join(datasets_dir, "zone_reference.csv"))
    zones.to_sql('zone_reference', engine, if_exists='replace', index=False)
    
    print("Loading survey_synthetic.csv...")
    survey = pd.read_csv(os.path.join(datasets_dir, "survey_synthetic.csv"))
    survey.to_sql('survey_synthetic', engine, if_exists='replace', index=False)
    
    print("Loading crime_dataset_india_final.csv...")
    crimes = pd.read_csv(os.path.join(datasets_dir, "crime_dataset_india_final.csv"))
    crimes.to_sql('crimes_master', engine, if_exists='replace', index=False)
    
    print("Updating PostGIS geometries...")
    with engine.connect() as conn:
        # Create PostGIS extension if it doesn't exist
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
        except Exception as e:
            print(f"Warning: Could not create postgis extension: {e}")

        # Add and update geom columns
        # For zone_reference
        conn.execute(text("ALTER TABLE zone_reference ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);"))
        conn.execute(text("UPDATE zone_reference SET geom = ST_SetSRID(ST_MakePoint(\"Zone_Longitude\", \"Zone_Latitude\"), 4326) WHERE \"Zone_Longitude\" IS NOT NULL;"))
        
        # For crimes_master
        conn.execute(text("ALTER TABLE crimes_master ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);"))
        conn.execute(text("UPDATE crimes_master SET geom = ST_SetSRID(ST_MakePoint(\"Longitude\", \"Latitude\"), 4326) WHERE \"Longitude\" IS NOT NULL;"))
        
        conn.commit()
        
    print("Data loaded successfully.")

if __name__ == "__main__":
    load_data()
