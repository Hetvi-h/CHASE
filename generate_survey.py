import pandas as pd
import numpy as np
import datetime
import os

def generate_survey_data(output_path, num_rows=15000):
    np.random.seed(42)

    # Load datasets
    datasets_dir = r"C:\PROJECTS\CHASE\datasets"
    crimes_path = os.path.join(datasets_dir, "crime_dataset_india_final.csv")
    zones_path = os.path.join(datasets_dir, "zone_reference.csv")
    
    crimes = pd.read_csv(crimes_path)
    zones = pd.read_csv(zones_path)

    # Calculate crime density per zone
    zone_crime_counts = crimes['Zone_ID'].value_counts().reset_index()
    zone_crime_counts.columns = ['Zone_ID', 'crime_count']

    # Merge with zones to ensure all zones are present
    zones = zones.merge(zone_crime_counts, on='Zone_ID', how='left')
    zones['crime_count'] = zones['crime_count'].fillna(0)

    # Normalize crime density to 0-1 using percentiles to ensure a flatter distribution
    if zones['crime_count'].max() > 0:
        zones['normalized_density'] = zones['crime_count'].rank(pct=True)
    else:
        zones['normalized_density'] = 0

    # Generate synthetic survey data
    zone_ids = zones['Zone_ID'].tolist()
    
    survey_data = {
        'survey_id': np.arange(1, num_rows + 1),
        'Zone_ID': np.random.choice(zone_ids, size=num_rows),
        'respondent_age_bracket': np.random.choice(['18-24', '25-34', '35-49', '50+'], size=num_rows, p=[0.25, 0.35, 0.25, 0.15]),
        'respondent_gender': np.random.choice(['Male', 'Female', 'Other'], size=num_rows, p=[0.55, 0.43, 0.02]),
        'time_of_day_band': np.random.choice(['Morning', 'Afternoon', 'Evening', 'Night'], size=num_rows),
        'visits_after_dark_frequency': np.random.choice(['Never', 'Rarely', 'Sometimes', 'Often'], size=num_rows),
    }
    
    df = pd.DataFrame(survey_data)
    
    # Map normalized density back to df
    density_map = dict(zip(zones['Zone_ID'], zones['normalized_density']))
    df['zone_density'] = df['Zone_ID'].map(density_map)

    # Generate safety rating: higher density -> lower rating
    # Mean rating = 5 - (zone_density * 3.5)
    df['mean_rating'] = 5 - (df['zone_density'] * 3.5)
    
    # Sample around mean
    def sample_rating(mean):
        val = int(np.round(np.random.normal(mean, 0.8)))
        return max(1, min(5, val))
    
    df['safety_rating'] = df['mean_rating'].apply(sample_rating)
    
    # Dependent logic for concern and improvement based on rating
    concerns = ['theft', 'harassment', 'poor_lighting', 'reckless_driving', 'other']
    improvements = ['CCTV', 'patrolling', 'lighting', 'awareness_programs', 'other']
    
    def assign_concern_improvement(row):
        rating = row['safety_rating']
        if rating <= 2:
            c = np.random.choice(['theft', 'harassment', 'poor_lighting'], p=[0.4, 0.3, 0.3])
            i = np.random.choice(['CCTV', 'patrolling', 'lighting'], p=[0.4, 0.4, 0.2])
        else:
            c = np.random.choice(concerns)
            i = np.random.choice(improvements)
        return pd.Series([c, i])
        
    df[['primary_concern', 'suggested_improvement']] = df.apply(assign_concern_improvement, axis=1)
    
    # Generate random response dates
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=180)
    
    def random_date(start, end):
        return start + datetime.timedelta(days=np.random.randint(0, max(1, (end - start).days)))
        
    df['response_date'] = [random_date(start_date, end_date) for _ in range(num_rows)]
    
    # Drop intermediate columns
    df = df.drop(columns=['zone_density', 'mean_rating'])
    
    # Output
    df.to_csv(output_path, index=False)
    print(f"Generated {num_rows} survey rows at {output_path}")

if __name__ == "__main__":
    generate_survey_data(r"C:\PROJECTS\CHASE\datasets\survey_synthetic.csv")
