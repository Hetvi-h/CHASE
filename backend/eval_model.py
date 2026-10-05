"""
Evaluate the Random Forest model with a proper train/test split and report
real accuracy and F1 scores.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
engine = create_engine(url)

print("Loading data from database...")
query = """
SELECT "Zone_ID", "Crime Domain", "Time of Occurrence", "Date of Occurrence", "Police Deployed"
FROM crimes_master
WHERE "Zone_ID" IS NOT NULL AND "Crime Domain" IS NOT NULL AND "Police Deployed" IS NOT NULL
"""
df = pd.read_sql(query, engine)
print(f"Loaded {len(df)} rows")

# Parse features
dt = pd.to_datetime(df['Time of Occurrence'], errors='coerce', dayfirst=True)
df['Hour'] = dt.dt.hour.fillna(0).astype(int)

date_col = pd.to_datetime(df['Date of Occurrence'], errors='coerce', dayfirst=True)
df['Month'] = date_col.dt.month.fillna(1).astype(int)
df['DayOfWeek'] = date_col.dt.dayofweek.fillna(0).astype(int)

zone_enc = LabelEncoder()
crime_enc = LabelEncoder()
df['Zone_ID_enc'] = zone_enc.fit_transform(df['Zone_ID'].astype(str))
df['Crime_Domain_enc'] = crime_enc.fit_transform(df['Crime Domain'].astype(str))

# Target: police_deployed > 10 = "High Risk"
df['target'] = (df['Police Deployed'] > 10).astype(int)
print(f"Class distribution: {df['target'].value_counts().to_dict()}")

FEATURE_NAMES = ['Zone_ID_enc', 'Crime_Domain_enc', 'Hour', 'DayOfWeek', 'Month']
X = df[FEATURE_NAMES]
y = df['target']

# 80/20 stratified train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Train: {len(X_train)} rows, Test: {len(X_test)} rows")

print("Training Random Forest (n_estimators=50, max_depth=10)...")
rf = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)

y_pred = rf.predict(X_test)
acc = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average='weighted')
f1_binary = f1_score(y_test, y_pred)

print(f"\n=== EVALUATION RESULTS ===")
print(f"Accuracy:              {acc:.4f}  ({acc*100:.2f}%)")
print(f"F1 (weighted):         {f1:.4f}")
print(f"F1 (binary, pos=1):    {f1_binary:.4f}")
print(f"\n--- Full Classification Report ---")
print(classification_report(y_test, y_pred, target_names=['Low Risk (0)', 'High Risk (1)']))
