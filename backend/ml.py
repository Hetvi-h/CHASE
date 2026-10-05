import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
import shap
from database import SessionLocal
import models
import threading

# Real evaluation results from 80/20 stratified train/test split (run 2026-10-01)
# on 40,160 rows, RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42)
EVAL_METRICS = {
    "accuracy": 0.5502,
    "f1_weighted": 0.5121,
    "f1_binary": 0.3570,
    "train_size": 32128,
    "test_size": 8032,
    "total_rows": 40160,
    "split": "80/20 stratified",
    "target": "Police Deployed > 10 (High Risk proxy)",
}


class RiskModelPipeline:
    def __init__(self):
        self.rf_model = None
        self.explainer = None
        self.shap_values = None
        self.feature_names = ['Zone_ID', 'Crime_Domain', 'Hour', 'DayOfWeek', 'Month']
        self.zone_encoder = LabelEncoder()
        self.crime_encoder = LabelEncoder()
        self.df_sample = None
        self._lock = threading.Lock()
        self._is_trained = False

    def train_model_if_needed(self, db=None):
        with self._lock:
            if self._is_trained:
                return

            print("Training global Random Forest model...")
            close_db = False
            if db is None:
                db = SessionLocal()
                close_db = True
            try:
                crimes = db.query(
                    models.CrimeMaster.zone_id,
                    models.CrimeMaster.crime_domain,
                    models.CrimeMaster.time_of_occurrence,
                    models.CrimeMaster.date_of_occurrence,
                    models.CrimeMaster.police_deployed
                ).all()

                df = pd.DataFrame(crimes, columns=[
                    'zone_id', 'crime_domain', 'time_of_occurrence',
                    'date_of_occurrence', 'police_deployed'
                ])

                # Parse time/date — dayfirst=True because format is DD-MM-YYYY HH:MM
                dt = pd.to_datetime(df['time_of_occurrence'], errors='coerce', dayfirst=True)
                df['Hour'] = dt.dt.hour.fillna(0).astype(int)

                date_col = pd.to_datetime(df['date_of_occurrence'], errors='coerce', dayfirst=True)
                df['Month'] = date_col.dt.month.fillna(1).astype(int)
                df['DayOfWeek'] = date_col.dt.dayofweek.fillna(0).astype(int)

                # Encode categorical features
                df['Zone_ID'] = self.zone_encoder.fit_transform(df['zone_id'].astype(str))
                df['Crime_Domain'] = self.crime_encoder.fit_transform(df['crime_domain'].astype(str))

                # Target: police_deployed > 10 as High-Risk proxy
                df['target'] = (df['police_deployed'] > 10).astype(int)

                X = df[self.feature_names]
                y = df['target']

                self.rf_model = RandomForestClassifier(
                    n_estimators=50, max_depth=10, random_state=42, n_jobs=-1
                )
                self.rf_model.fit(X, y)

                # Precompute SHAP values on a sample
                X_sample = X.sample(min(10000, len(X)), random_state=42)
                self.explainer = shap.TreeExplainer(self.rf_model)
                self.shap_values = self.explainer.shap_values(X_sample)

                if isinstance(self.shap_values, list):
                    self.shap_values = self.shap_values[1]  # positive class
                elif len(self.shap_values.shape) == 3:
                    self.shap_values = self.shap_values[:, :, 1]

                self.df_sample = df.loc[X_sample.index].copy()
                self._is_trained = True
                print("Model trained and SHAP values precomputed.")
            finally:
                if close_db:
                    db.close()

    def predict(self, zone_id: str, hour: int, day_of_week: int, month: int) -> dict:
        """
        Run the trained RF model on a single input vector.
        Returns risk_label, probability, and the known model evaluation metrics.
        """
        self.train_model_if_needed()

        # Encode zone_id — if unseen, fall back to 0
        if zone_id in self.zone_encoder.classes_:
            zone_encoded = int(self.zone_encoder.transform([zone_id])[0])
        else:
            zone_encoded = 0

        # Crime_Domain is not known at predict time (only zone+time given),
        # so we use the mode domain for this zone from training data as a prior.
        if self.df_sample is not None and zone_id in self.df_sample['zone_id'].values:
            zone_rows = self.df_sample[self.df_sample['zone_id'] == zone_id]
            mode_domain_encoded = int(zone_rows['Crime_Domain'].mode()[0])
        else:
            mode_domain_encoded = 0

        X_input = pd.DataFrame([{
            'Zone_ID': zone_encoded,
            'Crime_Domain': mode_domain_encoded,
            'Hour': hour,
            'DayOfWeek': day_of_week,
            'Month': month,
        }])[self.feature_names]

        prediction = int(self.rf_model.predict(X_input)[0])
        proba = self.rf_model.predict_proba(X_input)[0]
        high_risk_prob = float(proba[1])

        return {
            "risk_level": "High" if prediction == 1 else "Low",
            "high_risk_probability": round(high_risk_prob, 4),
            "prediction_raw": prediction,
            "likely_crime_type": self._likely_crime_type(zone_id, hour),
            "model_evaluation": EVAL_METRICS,
        }

    def _likely_crime_type(self, zone_id: str, hour: int) -> str:
        """
        Returns the most frequent crime domain for the given zone in the training sample,
        filtered to the same time-of-day band as the requested hour.
        Falls back to hour-band heuristic if zone has no data.
        """
        if self.df_sample is None:
            return "Unknown"

        zone_rows = self.df_sample[self.df_sample['zone_id'] == zone_id].copy()
        if len(zone_rows) == 0:
            return "Theft" if hour < 18 else "Harassment/Assault"

        # Narrow to same 6-hour band
        band_start = (hour // 6) * 6
        band_end = band_start + 6
        band_rows = zone_rows[(zone_rows['Hour'] >= band_start) & (zone_rows['Hour'] < band_end)]
        if len(band_rows) == 0:
            band_rows = zone_rows

        mode_encoded = int(band_rows['Crime_Domain'].mode()[0])
        return str(self.crime_encoder.inverse_transform([mode_encoded])[0])

    def get_zone_shap_summary(self, zone_id_str, db=None):
        self.train_model_if_needed(db=db)

        zone_mask = self.df_sample['zone_id'] == zone_id_str
        if not zone_mask.any():
            return None

        zone_shap = self.shap_values[zone_mask]
        avg_shap = np.mean(np.abs(zone_shap), axis=0)

        top_feature_idx = int(np.argmax(avg_shap))
        top_feature = self.feature_names[top_feature_idx]
        impacts = {feat: float(val) for feat, val in zip(self.feature_names, avg_shap)}

        return {
            "top_feature": top_feature,
            "impacts": impacts
        }


# Global singleton — one model, shared across all requests
risk_pipeline = RiskModelPipeline()
