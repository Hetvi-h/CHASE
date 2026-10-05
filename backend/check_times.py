import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
engine = create_engine(url)
query = 'SELECT "Time of Occurrence", "Date of Occurrence" FROM crimes_master LIMIT 5'
df = pd.read_sql(query, engine)
print(df)
