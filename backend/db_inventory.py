import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
url = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
engine = create_engine(url)

with engine.connect() as conn:
    tables = ['crimes_master', 'zone_reference', 'survey_synthetic', 'ncrb_city_totals_2023', 'profiles', 'audit_logs']
    for t in tables:
        try:
            count = conn.execute(text(f'SELECT COUNT(*) FROM {t}')).scalar()
            print(f'{t}: {count} rows')
        except Exception as e:
            print(f'{t}: ERROR - {e}')

    print("\n-- crimes_master columns --")
    r = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'crimes_master' ORDER BY ordinal_position"))
    for row in r:
        print(f'  {row[0]}: {row[1]}')

    print("\n-- zone_reference columns --")
    r = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'zone_reference' ORDER BY ordinal_position"))
    for row in r:
        print(f'  {row[0]}: {row[1]}')

    print("\n-- survey_synthetic columns --")
    r = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'survey_synthetic' ORDER BY ordinal_position"))
    for row in r:
        print(f'  {row[0]}: {row[1]}')

    print("\n-- profiles columns --")
    r = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'profiles' ORDER BY ordinal_position"))
    for row in r:
        print(f'  {row[0]}: {row[1]}')

    print("\n-- audit_logs columns --")
    r = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'audit_logs' ORDER BY ordinal_position"))
    for row in r:
        print(f'  {row[0]}: {row[1]}')

    print("\n-- ncrb_city_totals_2023 columns --")
    r = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'ncrb_city_totals_2023' ORDER BY ordinal_position"))
    for row in r:
        print(f'  {row[0]}: {row[1]}')

    print("\n-- RLS policies --")
    r = conn.execute(text("SELECT tablename, policyname, cmd, qual FROM pg_policies ORDER BY tablename"))
    for row in r:
        print(f'  [{row[0]}] {row[1]} ({row[2]}): {row[3]}')
