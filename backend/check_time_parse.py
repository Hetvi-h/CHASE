import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
engine = create_engine(url)
query = 'SELECT "Time of Occurrence" as time, "Date of Occurrence" as date FROM crimes_master LIMIT 10'
df = pd.read_sql(query, engine)
print("Raw:")
print(df)
df['hour'] = pd.to_datetime(df['time'], errors='coerce').dt.hour.fillna(0).astype(int)
df['day'] = pd.to_datetime(df['date'], errors='coerce').dt.dayofweek.fillna(0).astype(int)
print("Parsed:")
print(df)
