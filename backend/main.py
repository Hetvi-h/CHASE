from fastapi import FastAPI, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import math
import re
import os
import json
import threading
import requests as http_requests
from datetime import datetime
from jose import jwt, JWTError, jwk
from jose.utils import base64url_decode

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import SessionLocal, engine
import models
from ml import risk_pipeline
import pandas as pd
from voronoi import generate_voronoi_polygons

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="CHASE Geospatial API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_PROJECT_URL = os.getenv("SUPABASE_URL", "https://cwfwnuvcoxexxmnydoul.supabase.co")
SUPABASE_JWKS_URL = f"{SUPABASE_PROJECT_URL}/auth/v1/.well-known/jwks.json"

# ---------------------------------------------------------------------------
# JWKS key cache — fetched once at startup, refreshed if a kid is not found
# ---------------------------------------------------------------------------
_jwks_cache: dict = {}
_jwks_lock = threading.Lock()

def _refresh_jwks() -> dict:
    """Fetch Supabase's public JWKS and index by key ID (kid)."""
    try:
        resp = http_requests.get(SUPABASE_JWKS_URL, timeout=5)
        resp.raise_for_status()
        keys = resp.json().get("keys", [])
        return {k["kid"]: k for k in keys if "kid" in k}
    except Exception as e:
        print(f"[JWKS] Failed to refresh: {e}")
        return {}

def _get_public_key(kid: str):
    """Return the JWKS dict for the given kid, refreshing cache if necessary."""
    with _jwks_lock:
        if kid not in _jwks_cache:
            _jwks_cache.update(_refresh_jwks())
        return _jwks_cache.get(kid)

# Pre-load JWKS at import time (non-blocking; best-effort)
try:
    _jwks_cache.update(_refresh_jwks())
    print(f"[JWKS] Loaded {len(_jwks_cache)} public key(s) from Supabase.")
except Exception:
    pass

def get_current_user(authorization: Optional[str] = Header(None)):
    """Verify a Supabase-issued JWT against the project's public JWKS."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    token = authorization.split(" ")[1]
    try:
        # Peek at the header to find which key was used
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        alg = unverified_header.get("alg", "RS256")

        if kid is None:
            raise HTTPException(status_code=401, detail="Token missing kid header")

        jwks_key = _get_public_key(kid)
        if jwks_key is None:
            raise HTTPException(status_code=401, detail="Unknown signing key")

        # Build the public key object and verify the signature + claims
        public_key = jwk.construct(jwks_key, algorithm=alg)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[alg],
            options={"verify_aud": False},  # Supabase tokens have aud=authenticated
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")

def get_admin_user(user: dict = Depends(get_current_user), db: Session = Depends(lambda: next(get_db()))):
    profile = db.query(models.Profile).filter(models.Profile.id == user.get('sub')).first()
    if not profile or profile.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def log_audit(db: Session, user: dict, action: str, details: str, request: Request):
    log = models.AuditLog(
        user_id=user.get('sub'),
        user_email=user.get('email', ''),
        action=action,
        details=details,
        ip_address=request.client.host if request and request.client else '',
        created_at=str(datetime.now())
    )
    db.add(log)
    db.commit()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/auth/sync-profile")
@limiter.limit("10/minute")
def sync_profile(request: Request, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    uid = user.get("sub")
    email = user.get("email")
    # For Google Auth, name is often in user_metadata or just name
    name = user.get("user_metadata", {}).get("full_name", user.get("name", "Unknown"))
    
    profile = db.query(models.Profile).filter(models.Profile.id == uid).first()
    if not profile:
        profile = models.Profile(id=uid, email=email, full_name=name, role="viewer", created_at=str(datetime.now()))
        db.add(profile)
        db.commit()
    
    log_audit(db, user, "login", "User signed in", request)
    return {"status": "success"}

@app.get("/audit-logs")
@limiter.limit("30/minute")
def get_audit_logs(request: Request, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    uid = user.get("sub")
    profile = db.query(models.Profile).filter(models.Profile.id == uid).first()
    is_admin = profile and profile.role == 'admin'
    
    # Admins see all logs; regular users see only their own
    query = db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc())
    if not is_admin:
        query = query.filter(models.AuditLog.user_id == uid)
    logs = query.limit(200).all()
    return {"logs": [{"id": l.id, "user_email": l.user_email, "action": l.action, "details": l.details, "ip_address": l.ip_address, "created_at": l.created_at} for l in logs]}

@app.get("/states")
def get_states(db: Session = Depends(get_db)):
    states = db.query(models.CrimeMaster.state).filter(models.CrimeMaster.state.isnot(None)).distinct().all()
    return {"states": sorted([s[0] for s in states if s[0]])}

@app.get("/cities")
def get_cities(state: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.CrimeMaster.city).filter(models.CrimeMaster.city.isnot(None))
    if state:
        query = query.filter(models.CrimeMaster.state == state)
    cities = query.distinct().all()
    return {"cities": sorted([c[0] for c in cities if c[0]])}

@app.get("/zones")
def get_zones(city: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.ZoneReference)
    if city and city != "All Cities":
        query = query.filter(models.ZoneReference.city == city)
    zones = query.all()
    
    zones_data = [
        {"zone_id": z.zone_id, "lat": z.zone_latitude, "lng": z.zone_longitude, "weight": z.zone_weight, "city": z.city}
        for z in zones
    ]
    
    # Calculate voronoi polygons per city
    city_polygons = {}
    if zones_data:
        cities = set([z['city'] for z in zones_data])
        for c in cities:
            city_zones = [z for z in zones_data if z['city'] == c]
            if len(city_zones) > 0:
                c_lat = city_zones[0]['lat']
                c_lng = city_zones[0]['lng']
                polys = generate_voronoi_polygons(city_zones, c_lat, c_lng)
                city_polygons.update(polys)
                
    for z in zones_data:
        z['polygon'] = city_polygons.get(z['zone_id'], [])

    return {"zones": zones_data}

@app.get("/crime-domains")
def get_crime_domains(db: Session = Depends(get_db)):
    domains = db.query(models.CrimeMaster.crime_domain).filter(
        models.CrimeMaster.crime_domain.isnot(None)
    ).distinct().all()
    return {"domains": sorted([d[0] for d in domains if d[0]])}

@app.get("/hotspots")
def get_hotspots(city: Optional[str] = None, hour: Optional[int] = None, crime_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(
        models.CrimeMaster.latitude, 
        models.CrimeMaster.longitude, 
        models.CrimeMaster.crime_domain,
        models.CrimeMaster.is_synthetic_row,
        models.CrimeMaster.report_number,
        models.CrimeMaster.time_of_occurrence,
        models.CrimeMaster.zone_id
    )
    if city and city != "All Cities":
        query = query.filter(models.CrimeMaster.city == city)
    
    if crime_type:
        query = query.filter(models.CrimeMaster.crime_domain == crime_type)
    
    if hour is not None:
        hour_str = f" {hour:02d}:"
        query = query.filter(models.CrimeMaster.time_of_occurrence.like(f"%{hour_str}%"))
        
    hotspots = query.limit(10000).all() # Limit to prevent browser crash
    return {"hotspots": [{"id": h[4], "lat": h[0], "lng": h[1], "type": h[2], "synthetic": h[3], "time": h[5], "zone_id": h[6]} for h in hotspots if h[0] is not None]}

_zone_scores_cache = {}

@app.get("/zone-scores")
def get_zone_scores(city: Optional[str] = None, db: Session = Depends(get_db)):
    cache_key = city or "All Cities"
    if cache_key in _zone_scores_cache:
        return _zone_scores_cache[cache_key]

    # Composite Score = 100 - (w1 * crime_density + w2 * (5-rating)*20)
    query = db.query(
        models.CrimeMaster.zone_id,
        func.count(models.CrimeMaster.report_number)
    )
    if city and city != "All Cities":
        query = query.filter(models.CrimeMaster.city == city)
    crime_counts = query.group_by(models.CrimeMaster.zone_id).all()
    
    zone_ids = [row[0] for row in crime_counts if row[0] is not None]
    
    ratings_q = db.query(
        models.SurveySynthetic.zone_id,
        func.avg(models.SurveySynthetic.safety_rating)
    ).filter(models.SurveySynthetic.zone_id.in_(zone_ids)).group_by(models.SurveySynthetic.zone_id).all()
    ratings_dict = {r[0]: float(r[1]) for r in ratings_q if r[0] is not None and r[1] is not None}
    
    scores = []
    for zone_id, count in crime_counts:
        if zone_id is None: continue
        
        avg_rating = ratings_dict.get(zone_id, 3.0)
        normalized_density = min(1.0, count / 1000.0) 
        
        w1, w2 = 0.6, 0.4
        score = 100 - (w1 * normalized_density * 100 + w2 * (5 - avg_rating) * 20)
        
        scores.append({
            "zone_id": zone_id,
            "score": max(0, min(100, round(score, 1))),
            "crime_count": count,
            "avg_safety_rating": round(avg_rating, 2)
        })
        
    _zone_scores_cache[cache_key] = {"scores": scores}
    return {"scores": scores}

@app.get("/stats/zones")
def get_zone_stats(city: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(
        models.CrimeMaster.zone_id,
        func.count(models.CrimeMaster.report_number).label('count')
    )
    if city and city != "All Cities":
        query = query.filter(models.CrimeMaster.city == city)
    zones = query.group_by(models.CrimeMaster.zone_id).all()
    
    return {"zones": [{"zone_id": z[0], "count": z[1]} for z in zones if z[0] is not None]}

@app.get("/stats/time-heatmap")
def get_time_heatmap(city: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.CrimeMaster.time_of_occurrence, models.CrimeMaster.date_of_occurrence)
    if city and city != "All Cities":
        query = query.filter(models.CrimeMaster.city == city)
    crimes = query.all()
    df = pd.DataFrame(crimes, columns=['time', 'date'])
    if len(df) == 0:
        return {"heatmap": []}
    df['hour'] = pd.to_datetime(df['time'], errors='coerce', dayfirst=True).dt.hour.fillna(0).astype(int)
    df['day'] = pd.to_datetime(df['date'], errors='coerce', dayfirst=True).dt.dayofweek.fillna(0).astype(int)
    grouped = df.groupby(['hour', 'day']).size().reset_index(name='count')
    return {"heatmap": grouped.to_dict('records')}

@app.get("/stats/monthly-trend")
def get_monthly_trend(city: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.CrimeMaster.date_of_occurrence)
    if city and city != "All Cities":
        query = query.filter(models.CrimeMaster.city == city)
    crimes = query.all()
    
    df = pd.DataFrame(crimes, columns=['date'])
    if len(df) == 0:
        return {"trend": []}
        
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    df['month'] = df['date'].dt.to_period('M')
    grouped = df.groupby('month').size().reset_index(name='count')
    grouped['month'] = grouped['month'].astype(str)
    grouped = grouped.sort_values('month')
    return {"trend": grouped.to_dict('records')}

@app.get("/stats/crime-types-by-zone")
def get_crime_types_by_zone(city: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(
        models.CrimeMaster.zone_id,
        models.CrimeMaster.crime_domain,
        func.count().label('count')
    )
    if city and city != "All Cities":
        query = query.filter(models.CrimeMaster.city == city)
    crimes = query.group_by(
        models.CrimeMaster.zone_id,
        models.CrimeMaster.crime_domain
    ).all()
    
    # Process into format: [{zone_id: 'Zone 1', 'Violent Crime': 10, 'Other Crime': 20, ...}]
    data = {}
    for zone, domain, count in crimes:
        if not zone or not domain: continue
        if zone not in data:
            data[zone] = {"zone_id": zone}
        data[zone][domain] = count
        
    return {"data": list(data.values())}

_recommendations_cache = {}

@app.get("/recommendations/{zone_id}")
def get_recommendations(zone_id: str, request: Request = None, user: dict = None, db: Session = Depends(get_db)):
    if zone_id in _recommendations_cache:
        cached = _recommendations_cache[zone_id]
        if request and user:
            log_audit(db, user, "viewed_action_plan", f"Viewed action plan for zone {zone_id} (cached)", request)
        return cached

    shap_summary = risk_pipeline.get_zone_shap_summary(zone_id, db=db)
    
    surveys = db.query(models.SurveySynthetic.primary_concern, models.SurveySynthetic.suggested_improvement).filter(models.SurveySynthetic.zone_id == zone_id).all()
    df = pd.DataFrame(surveys, columns=['concern', 'improvement'])
    
    if len(df) > 0:
        top_concern = df['concern'].mode()[0] if not df['concern'].mode().empty else "general safety"
        top_improvement = df['improvement'].mode()[0] if not df['improvement'].mode().empty else "community policing"
    else:
        top_concern = "general safety"
        top_improvement = "community policing"
        
    top_feature = shap_summary['top_feature'] if shap_summary else "historical trends"
    
    sentence = f"This zone's risk is primarily driven by {top_feature} — residents most frequently cite {top_concern} and recommend {top_improvement}."
    
    result = {
        "sentence": sentence,
        "shap_summary": shap_summary,
        "top_concern": top_concern,
        "top_improvement": top_improvement
    }
    _recommendations_cache[zone_id] = result
    return result

class RiskRequest(BaseModel):
    zone_id: str
    hour: int
    day_of_week: int
    month: int

@app.post("/predict-risk")
@limiter.limit("100/minute")
def predict_risk(request: Request, req: RiskRequest, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Run the trained Random Forest model to predict risk level for a given
    zone/time combination. Returns the model's actual .predict() output,
    .predict_proba() high-risk probability, likely crime type (from zone
    training data), and the real evaluation metrics from the 80/20 split.
    """
    result = risk_pipeline.predict(
        zone_id=req.zone_id,
        hour=req.hour,
        day_of_week=req.day_of_week,
        month=req.month,
    )
    log_audit(db, user, "risk_prediction", f"Predicted risk for zone {req.zone_id} → {result.get('risk_level')} ({result.get('high_risk_probability', 0)*100:.1f}%)", request)
    return result

@app.get("/cases")
def get_cases(
    city: Optional[str] = None, 
    zone_id: Optional[str] = None, 
    crime_domain: Optional[str] = None, 
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 20, 
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(
        models.CrimeMaster.report_number,
        models.CrimeMaster.date_of_occurrence,
        models.CrimeMaster.time_of_occurrence,
        models.CrimeMaster.zone_id,
        models.CrimeMaster.crime_domain,
        models.CrimeMaster.crime_description,
        models.CrimeMaster.is_synthetic_row
    )
    if city and city != "All Cities":
        query = query.filter(models.CrimeMaster.city == city)
    
    if zone_id:
        query = query.filter(models.CrimeMaster.zone_id == zone_id)
    if crime_domain:
        query = query.filter(models.CrimeMaster.crime_domain == crime_domain)
    if start_date:
        query = query.filter(models.CrimeMaster.date_of_occurrence >= start_date)
    if end_date:
        query = query.filter(models.CrimeMaster.date_of_occurrence <= end_date)
        
    total_count = query.count()
    cases = query.order_by(models.CrimeMaster.report_number.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total_count,
        "cases": [
            {
                "id": c[0],
                "date": str(c[1]),
                "time": str(c[2]),
                "zone_id": c[3],
                "type": c[4],
                "description": c[5],
                "synthetic": c[6]
            } for c in cases
        ]
    }

class ChatbotPipeline:
    def __init__(self, db_session_factory):
        self.db_factory = db_session_factory

    def process_message(self, message: str, city: str):
        message = message.lower()
        import re
        
        # Try to extract the zone number directly
        zone_match = re.search(r'zone_?\s*(\d+)', message)
        if not zone_match:
            return "I am an analytical assistant configured for localized crime data. Please specify a zone number (e.g., 'Zone 2' or 'Zone_2') so I can fetch the specific data for you. You can ask about incident counts, risk drivers, safety scores, or top crime types."
            
        zone_num = zone_match.group(1)
        zone_id = f"{city}_Zone_{zone_num}"
        
        # Determine intent flexibly
        if re.search(r'(how many|count|number of).*(crimes|cases|incidents|reports)', message):
            intent = 'count'
        elif re.search(r'(what is the risk|risk|how to improve|driver|factor)', message):
            intent = 'risk'
        elif re.search(r'(composite score|safety score|score|safe)', message):
            intent = 'score'
        elif re.search(r'(types of crime|what crimes|which crimes|crime types|domain)', message):
            intent = 'types'
        else:
            return f"I see you're asking about {zone_id}. You can ask me about its incident count, risk drivers, safety score, or top crime types."

        db = self.db_factory()
        try:
            if intent == 'count':
                count = db.query(models.CrimeMaster).filter(
                    models.CrimeMaster.city == city,
                    models.CrimeMaster.zone_id == zone_id
                ).count()
                return f"Based on the database, there have been {count} incidents recorded in {zone_id}."
                
            elif intent == 'risk':
                shap_summary = risk_pipeline.get_zone_shap_summary(zone_id)
                if shap_summary:
                    top_feature = shap_summary['top_feature']
                    return f"The ML model indicates the primary driver of risk in {zone_id} is currently {top_feature}."
                return f"I couldn't analyze the risk for {zone_id} at this time."
                
            elif intent == 'score':
                crime_count = db.query(models.CrimeMaster).filter(models.CrimeMaster.zone_id == zone_id).count()
                avg_rating = db.query(func.avg(models.SurveySynthetic.safety_rating)).filter(models.SurveySynthetic.zone_id == zone_id).scalar() or 3.0
                normalized_density = min(1.0, crime_count / 1000.0) 
                w1, w2 = 0.6, 0.4
                score = 100 - (w1 * normalized_density * 100 + w2 * (5 - float(avg_rating)) * 20)
                score = max(0, min(100, round(score, 1)))
                return f"The composite safety score for {zone_id} is {score}/100. This is based on a crime density of {crime_count} incidents and a community safety rating of {round(float(avg_rating), 2)}/5."
                
            elif intent == 'types':
                types = db.query(models.CrimeMaster.crime_domain, func.count(models.CrimeMaster.report_number)).filter(
                    models.CrimeMaster.city == city,
                    models.CrimeMaster.zone_id == zone_id
                ).group_by(models.CrimeMaster.crime_domain).order_by(func.count(models.CrimeMaster.report_number).desc()).limit(3).all()
                if types:
                    types_str = ", ".join([f"{t[0]} ({t[1]} cases)" for t in types])
                    return f"The most frequent crimes reported in {zone_id} are: {types_str}."
                return f"No crimes recorded for {zone_id}."
                
        except Exception as e:
            return f"An error occurred while processing your request: {str(e)}"
        finally:
            db.close()

chatbot = ChatbotPipeline(SessionLocal)

class ChatRequest(BaseModel):
    message: str
    city: str

@app.post("/chat")
@limiter.limit("20/minute")
def chat_endpoint(request: Request, req: ChatRequest, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    response_text = chatbot.process_message(req.message, req.city)
    log_audit(db, user, "chatbot_query", f"City={req.city} | Q: {req.message[:100]}", request)
    return {"response": response_text}


from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class PatrolAllocationRequest(BaseModel):
    city: str
    total_units: int

@app.post("/allocate-patrols")
def allocate_patrols(request: Request, req: PatrolAllocationRequest, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    log_audit(db, user, "patrol_allocation", f"Generated patrol plan for {req.city} with {req.total_units} units", request)
    # 1. Get zones and risk scores
    scores_data = get_zone_scores(req.city, db=db)
    zones = scores_data.get("scores", [])
    if not zones:
        return {"allocations": []}

    # Sort descending by risk score
    zones = sorted(zones, key=lambda x: x["score"], reverse=True)
    
    total_score = sum(z["score"] for z in zones)
    
    allocations = []
    remaining_units = req.total_units
    
    # Proportional allocation
    for i, z in enumerate(zones):
        if total_score > 0:
            prop = z["score"] / total_score
        else:
            prop = 1.0 / len(zones)
            
        units = int(round(prop * req.total_units))
        
        # Adjust for rounding errors on the last item
        if i == len(zones) - 1:
            units = remaining_units
        elif units > remaining_units:
            units = remaining_units
            
        remaining_units -= units
        
        allocations.append({
            "zone_id": z["zone_id"],
            "city": req.city,
            "risk_score": z["score"],
            "units_assigned": units
        })
        
    return {"allocations": sorted(allocations, key=lambda x: x["units_assigned"], reverse=True)}

@app.get("/resourcing-gap")
def get_resourcing_gap(city: str, db: Session = Depends(get_db)):
    # 1. Get zones and risk scores
    scores_data = get_zone_scores(city, db=db)
    zones = scores_data.get("scores", [])
    
    # 2. Get average police deployed per zone
    police_data = db.query(
        models.CrimeMaster.zone_id,
        func.avg(models.CrimeMaster.police_deployed)
    ).filter(models.CrimeMaster.city == city).group_by(models.CrimeMaster.zone_id).all()
    
    police_dict = {z[0]: float(z[1] or 0) for z in police_data if z[0]}
    
    # Normalization helper
    max_risk = max([z["score"] for z in zones] + [1])
    max_police = max(police_dict.values()) if police_dict else 1
    
    gaps = []
    for z in zones:
        zone_id = z["zone_id"]
        risk = z["score"]
        police = police_dict.get(zone_id, 0)
        
        norm_risk = risk / max_risk
        norm_police = police / max_police
        
        gap_score = norm_risk - norm_police
        
        gaps.append({
            "zone_id": zone_id,
            "risk_score": risk,
            "avg_police_deployed": round(police, 2),
            "gap_score": round(gap_score, 3)
        })
        
    gaps = sorted(gaps, key=lambda x: x["gap_score"], reverse=True)
    return {"gaps": gaps}

@app.get("/reports/zone/{zone_id}/pdf")
def generate_zone_pdf(zone_id: str, request: Request = None, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    log_audit(db, user, "pdf_download", f"Downloaded PDF report for zone {zone_id}", request)
    # Gather data
    city = zone_id.split("_")[0] if "_" in zone_id else "Unknown"
    scores_data = get_zone_scores(city, db=db)
    zone_score = next((z for z in scores_data.get("scores", []) if z["zone_id"] == zone_id), None)
    
    rec_data = get_recommendations(zone_id, db=db)
    
    pdf_path = f"{zone_id}_report.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph(f"Zone Risk Report: {zone_id}", styles['Title']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph(f"City: {city}", styles['Normal']))
    if zone_score:
        story.append(Paragraph(f"Risk Score: {zone_score['score']}", styles['Normal']))
        story.append(Paragraph(f"Total Incident Count: {zone_score['crime_count']}", styles['Normal']))
    
    story.append(Spacer(1, 12))
    story.append(Paragraph("Action Plan & Recommendations", styles['Heading2']))
    
    if rec_data:
        story.append(Paragraph(f"<b>Top Concern:</b> {rec_data.get('top_concern', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"<b>Top Improvement:</b> {rec_data.get('top_improvement', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        shap = rec_data.get('shap_summary')
        if shap:
            story.append(Paragraph(f"<b>Primary Risk Driver:</b> {shap.get('top_feature', 'N/A')}", styles['Normal']))
            
    doc.build(story)
    
    return FileResponse(pdf_path, filename=f"{zone_id}_RiskReport.pdf")

@app.get("/reports/city/{city}/pdf")
def generate_city_pdf(city: str, db: Session = Depends(get_db)):
    scores_data = get_zone_scores(city, db=db)
    zones = sorted(scores_data.get("scores", []), key=lambda x: x["score"], reverse=True)
    
    pdf_path = f"{city}_report.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph(f"City Risk Report: {city}", styles['Title']))
    story.append(Spacer(1, 12))
    
    data = [["Zone ID", "Risk Score", "Incidents", "Avg Safety Rating"]]
    for z in zones:
        data.append([z["zone_id"], str(z["score"]), str(z["crime_count"]), str(z["avg_safety_rating"])])
        
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    
    story.append(t)
    doc.build(story)
    
    return FileResponse(pdf_path, filename=f"{city}_RiskReport.pdf")

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
def add_case(request: Request, req: NewCaseRequest, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    global _zone_scores_cache, _recommendations_cache
    _zone_scores_cache.clear()
    _recommendations_cache.clear()
    log_audit(db, user, "added_case", f"Filed new case in {req.city} / {req.zone_id} — domain: {req.crime_domain}", request)
    
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
