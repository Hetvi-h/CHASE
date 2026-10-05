from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
load_dotenv()
url = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
engine = create_engine(url)
with engine.connect() as conn:
    rows = conn.execute(text("SELECT tablename, policyname, qual FROM pg_policies ORDER BY tablename")).fetchall()
    for r in rows:
        print(f'[{r[0]}] {r[1]}')
        print(f'  QUAL: {str(r[2])[:200]}')
        print()
