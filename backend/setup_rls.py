import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    print("Creating profiles and audit_logs tables...")
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS profiles (
        id UUID PRIMARY KEY,
        email TEXT,
        full_name TEXT,
        role TEXT DEFAULT 'viewer',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """))

    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id SERIAL PRIMARY KEY,
        user_id UUID,
        user_email TEXT,
        action TEXT,
        details TEXT,
        ip_address TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """))

    print("Enabling RLS on all tables...")
    tables = [
        "crimes_master", "zone_reference", "survey_synthetic",
        "ncrb_city_totals_2023", "profiles", "audit_logs"
    ]
    for table in tables:
        conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))

    print("Creating RLS policies...")
    
    # Drop existing policies if any
    for table in tables:
        try:
            conn.execute(text(f"DROP POLICY IF EXISTS {table}_read ON {table};"))
            conn.execute(text(f"DROP POLICY IF EXISTS {table}_admin ON {table};"))
            conn.execute(text(f"DROP POLICY IF EXISTS {table}_self ON {table};"))
        except:
            pass

    # Viewer/Admin read-only policies for data tables
    for table in ["crimes_master", "zone_reference", "survey_synthetic", "ncrb_city_totals_2023"]:
        conn.execute(text(f"""
        CREATE POLICY {table}_read ON {table}
        FOR SELECT
        USING (
            (SELECT role FROM profiles WHERE id = auth.uid()) IN ('viewer', 'admin')
            OR
            auth.uid() IS NULL -- temp for public access if needed, but we want it restricted
        );
        """))

    # Profiles table: select own row, admin selects all
    conn.execute(text("""
    CREATE POLICY profiles_self ON profiles FOR SELECT USING (auth.uid() = id);
    CREATE POLICY profiles_admin ON profiles FOR SELECT USING ((SELECT role FROM profiles WHERE id = auth.uid()) = 'admin');
    """))

    # Audit Logs: admin only select
    conn.execute(text("""
    CREATE POLICY audit_logs_admin ON audit_logs FOR SELECT USING ((SELECT role FROM profiles WHERE id = auth.uid()) = 'admin');
    """))

    print("Done setting up tables and RLS.")
