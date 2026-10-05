import os

main_py_path = 'C:/PROJECTS/CHASE/backend/main.py'
with open(main_py_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_func = '''    def process_message(self, message: str, city: str):
        message = message.lower()
        
        intent_cases_count = re.search(r'how many (crimes|cases|incidents).*in zone\s*(_?[0-9]+)', message)
        intent_risk = re.search(r'(what is the risk|risk|how to improve).*in zone\s*(_?[0-9]+)', message)
        intent_score = re.search(r'(composite score|safety score|score).*in zone\s*(_?[0-9]+)', message)
        intent_types = re.search(r'(what are the types of crime|types of crime|what crimes).*in zone\s*(_?[0-9]+)', message)
        
        db = self.db_factory()
        try:
            if intent_cases_count:
                zone_num = intent_cases_count.group(2).replace('_', '').replace('zone', '')
                zone_id = f"{city}_Zone_{zone_num}"
                count = db.query(models.CrimeMaster).filter(
                    models.CrimeMaster.city == city,
                    models.CrimeMaster.zone_id == zone_id
                ).count()
                return f"Based on the database, there have been {count} incidents recorded in {zone_id}."
                
            elif intent_risk:
                zone_num = intent_risk.group(2).replace('_', '').replace('zone', '')
                zone_id = f"{city}_Zone_{zone_num}"
                shap_summary = risk_pipeline.get_zone_shap_summary(zone_id)
                if shap_summary:
                    top_feature = shap_summary['top_feature']
                    return f"The ML model indicates the primary driver of risk in {zone_id} is currently {top_feature}."
                return f"I couldn't analyze the risk for {zone_id} at this time."
                
            elif intent_score:
                zone_num = intent_score.group(2).replace('_', '').replace('zone', '')
                zone_id = f"{city}_Zone_{zone_num}"
                crime_count = db.query(models.CrimeMaster).filter(models.CrimeMaster.zone_id == zone_id).count()
                avg_rating = db.query(func.avg(models.SurveySynthetic.safety_rating)).filter(models.SurveySynthetic.zone_id == zone_id).scalar() or 3.0
                normalized_density = min(1.0, crime_count / 1000.0) 
                w1, w2 = 0.6, 0.4
                score = 100 - (w1 * normalized_density * 100 + w2 * (5 - avg_rating) * 20)
                score = max(0, min(100, round(score, 1)))
                return f"The composite safety score for {zone_id} is {score}/100. This is based on a crime density of {crime_count} incidents and a community safety rating of {round(avg_rating, 2)}/5."
                
            elif intent_types:
                zone_num = intent_types.group(2).replace('_', '').replace('zone', '')
                zone_id = f"{city}_Zone_{zone_num}"
                domains = db.query(models.CrimeMaster.crime_domain, func.count(models.CrimeMaster.report_number))\\
                    .filter(models.CrimeMaster.zone_id == zone_id)\\
                    .group_by(models.CrimeMaster.crime_domain)\\
                    .order_by(func.count(models.CrimeMaster.report_number).desc())\\
                    .limit(3).all()
                if not domains:
                    return f"No specific crime data found for {zone_id}."
                domain_str = ", ".join([f"{d[0]} ({d[1]} cases)" for d in domains])
                return f"The most frequent crime types in {zone_id} are: {domain_str}."
                
            else:
                return "I am an analytical assistant configured for localized crime data. This query appears to be outside my current analytical scope. Try asking about incident counts, risk drivers, top crimes, or safety scores for specific zones."
        except Exception as e:
            return f"An error occurred while processing your request: {str(e)}"
        finally:
            db.close()'''

new_func = '''    def process_message(self, message: str, city: str):
        message = message.lower()
        
        import re
        # Try to extract the zone number, e.g. from "zone 2", "zone_2", "ludhiana_zone_2"
        zone_match = re.search(r'zone_?\\s*(\\d+)', message)
        if not zone_match:
            return "I am an analytical assistant configured for localized crime data. Please specify a zone number (e.g., 'Zone 2' or 'Zone_2') so I can fetch the specific data for you. You can ask about incident counts, risk drivers, safety scores, or top crime types."
            
        zone_num = zone_match.group(1)
        zone_id = f"{city}_Zone_{zone_num}"
        
        # Determine intent
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
                score = 100 - (w1 * normalized_density * 100 + w2 * (5 - avg_rating) * 20)
                score = max(0, min(100, round(score, 1)))
                return f"The composite safety score for {zone_id} is {score}/100. This is based on a crime density of {crime_count} incidents and a community safety rating of {round(avg_rating, 2)}/5."
                
            elif intent == 'types':
                domains = db.query(models.CrimeMaster.crime_domain, func.count(models.CrimeMaster.report_number))\\
                    .filter(models.CrimeMaster.zone_id == zone_id)\\
                    .group_by(models.CrimeMaster.crime_domain)\\
                    .order_by(func.count(models.CrimeMaster.report_number).desc())\\
                    .limit(3).all()
                if not domains:
                    return f"No specific crime data found for {zone_id}."
                domain_str = ", ".join([f"{d[0]} ({d[1]} cases)" for d in domains])
                return f"The most frequent crime types in {zone_id} are: {domain_str}."
                
        except Exception as e:
            return f"An error occurred while processing your request: {str(e)}"
        finally:
            db.close()'''

if old_func in content:
    content = content.replace(old_func, new_func)
    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched chatbot function successfully.")
else:
    print("Could not find the old function exact string.")
