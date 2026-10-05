import os

main_py_path = 'C:/PROJECTS/CHASE/backend/main.py'
with open(main_py_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add caches
if '_zone_scores_cache = {}' not in content:
    content = content.replace(
        'def get_zone_scores(city: Optional[str] = None, db: Session = Depends(get_db)):',
        '''
_zone_scores_cache = {}

def get_zone_scores(city: Optional[str] = None, db: Session = Depends(get_db)):
    cache_key = city or "All Cities"
    if cache_key in _zone_scores_cache:
        return _zone_scores_cache[cache_key]
'''
    )
    content = content.replace(
        '    return {"scores": scores}',
        '    _zone_scores_cache[cache_key] = {"scores": scores}\n    return {"scores": scores}'
    )

if '_recommendations_cache = {}' not in content:
    content = content.replace(
        'def get_recommendations(zone_id: str, db: Session = Depends(get_db)):',
        '''
_recommendations_cache = {}

def get_recommendations(zone_id: str, db: Session = Depends(get_db)):
    if zone_id in _recommendations_cache:
        return _recommendations_cache[zone_id]
'''
    )
    content = content.replace(
        '        "top_improvement": top_improvement\n    }',
        '        "top_improvement": top_improvement\n    }\n    _recommendations_cache[zone_id] = result\n    return result'
    )
    content = content.replace(
        '    return {',
        '    result = {'
    )

if 'class NewCaseRequest(BaseModel):' not in content:
    new_case_code = '''
class NewCaseRequest(BaseModel):
    date_of_occurrence: str
    time_of_occurrence: str
    city: str
    zone_id: str
    crime_domain: str
    crime_description: Optional[str] = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None

@app.post("/cases")
def add_case(req: NewCaseRequest, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _zone_scores_cache, _recommendations_cache
    _zone_scores_cache.clear()
    _recommendations_cache.clear()
    
    max_id = db.query(func.max(models.CrimeMaster.report_number)).scalar() or 0
    new_id = max_id + 1
    
    new_case = models.CrimeMaster(
        report_number=new_id,
        date_of_occurrence=req.date_of_occurrence,
        time_of_occurrence=req.time_of_occurrence,
        city=req.city,
        zone_id=req.zone_id,
        crime_domain=req.crime_domain,
        crime_description=req.crime_description,
        latitude=req.latitude,
        longitude=req.longitude,
        is_synthetic_row=False,
        police_deployed=2,
        state="Unknown"
    )
    db.add(new_case)
    db.commit()
    
    csv_path = os.path.join(os.path.dirname(__file__), "..", "datasets", "crimes_master.csv")
    if os.path.exists(csv_path):
        try:
            import pandas as pd
            cols = pd.read_csv(csv_path, nrows=0).columns
            row_dict = {
                "Report Number": new_id,
                "Date of Occurrence": req.date_of_occurrence,
                "Time of Occurrence": req.time_of_occurrence,
                "City": req.city,
                "Zone_ID": req.zone_id,
                "Crime Domain": req.crime_domain,
                "Crime Description": req.crime_description,
                "Latitude": req.latitude,
                "Longitude": req.longitude,
                "Is_Synthetic_Row": False,
                "Police Deployed": 2,
                "State": "Unknown"
            }
            row_df = pd.DataFrame([{c: row_dict.get(c, None) for c in cols}])
            row_df.to_csv(csv_path, mode='a', header=False, index=False)
        except Exception as e:
            print("Failed to append to CSV:", e)
            
    return {"status": "success", "id": new_id}
'''
    content += new_case_code

with open(main_py_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched main.py")
