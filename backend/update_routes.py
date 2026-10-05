import re

with open('C:/PROJECTS/CHASE/backend/main.py', 'r') as f:
    code = f.read()

# For standard GET/POST endpoints that don't have limit or request yet
def repl(m):
    decorator = m.group(1)
    func_def = m.group(2)
    
    # If already has limiter or is one of the ones we manually added
    if '@limiter' in decorator or 'sync_profile' in func_def or 'get_audit_logs' in func_def:
        return m.group(0)

    # Determine rate limit
    limit = "100/minute"
    if '/chat' in decorator:
        limit = "20/minute"
    elif '/reports/' in decorator:
        limit = "10/minute"

    # Determine auth
    auth = "user: dict = Depends(get_current_user), "
    if '/cases' in decorator or '/reports/' in decorator:
        auth = "user: dict = Depends(get_admin_user), "
        
    # Determine logging
    action = ""
    if '/cases' in decorator:
        action = "log_audit(db, user, 'case_browser_view', 'Viewed cases', request)\n    "
    elif '/reports/zone' in decorator:
        action = "log_audit(db, user, 'pdf_export_zone', f'Exported zone {zone_id}', request)\n    "
    elif '/reports/city' in decorator:
        action = "log_audit(db, user, 'pdf_export_city', f'Exported city {city}', request)\n    "
    elif '/allocate-patrols' in decorator:
        action = "log_audit(db, user, 'patrol_allocation', 'Allocated patrols', request)\n    "

    # Inject request: Request
    if 'request: Request' not in func_def:
        func_def = func_def.replace('(', f'(request: Request, {auth}', 1)
        
    # Inject action log
    if action:
        # Find where the function block starts
        idx = func_def.find(':\n')
        if idx != -1:
            func_def = func_def[:idx+2] + '    ' + action + func_def[idx+2:]

    return f"{decorator}\n@limiter.limit(\"{limit}\")\n{func_def}"

# Regex to match route decorator and function definition
pattern = r'(@app\.(?:get|post)\("[^"]+"\))\n(def \w+\([^)]+\)(?: \-\> [^:]+)?:(?:\n(?:    .*)*)?)'
new_code = re.sub(pattern, repl, code, flags=re.MULTILINE)

with open('C:/PROJECTS/CHASE/backend/main.py', 'w') as f:
    f.write(new_code)
print("Updated main.py")
