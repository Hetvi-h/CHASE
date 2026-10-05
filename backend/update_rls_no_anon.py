"""
Update RLS SELECT policies on data tables to require auth.uid() IS NOT NULL.
Removes the previous anonymous-read allowance.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
url = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
engine = create_engine(url)

data_tables = [
    "crimes_master",
    "zone_reference",
    "survey_synthetic",
    "ncrb_city_totals_2023",
]

with engine.begin() as conn:
    for table in data_tables:
        # Drop old policy that allowed anon reads
        conn.execute(text(f"DROP POLICY IF EXISTS {table}_read ON {table};"))

        # New policy: only roles viewer or admin, AND must be authenticated
        conn.execute(text(f"""
            CREATE POLICY {table}_read ON {table}
            FOR SELECT
            USING (
                auth.uid() IS NOT NULL
                AND (SELECT role FROM profiles WHERE id = auth.uid()) IN ('viewer', 'admin')
            );
        """))
        print(f"Updated policy: {table}_read — requires auth.uid() IS NOT NULL + role check")
