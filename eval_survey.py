import pandas as pd
import numpy as np
import os

datasets_dir = r"C:\PROJECTS\CHASE\datasets"
survey_path = os.path.join(datasets_dir, "survey_synthetic.csv")
crimes_path = os.path.join(datasets_dir, "crime_dataset_india_final.csv")

survey = pd.read_csv(survey_path)
crimes = pd.read_csv(crimes_path)

print("Safety Rating Distribution:")
print(survey['safety_rating'].value_counts().sort_index())

# Calculate crime count per zone
zone_crimes = crimes['Zone_ID'].value_counts().reset_index()
zone_crimes.columns = ['Zone_ID', 'crime_count']

# Calculate avg safety rating per zone
zone_ratings = survey.groupby('Zone_ID')['safety_rating'].mean().reset_index()
zone_ratings.columns = ['Zone_ID', 'avg_rating']

# Merge and calculate correlation
merged = pd.merge(zone_ratings, zone_crimes, on='Zone_ID', how='inner')
correlation = merged['avg_rating'].corr(merged['crime_count'])

print(f"\nCorrelation between crime count and avg safety rating: {correlation:.4f}")
