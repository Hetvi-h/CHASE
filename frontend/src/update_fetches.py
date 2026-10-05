import re

with open('C:/PROJECTS/CHASE/frontend/src/App.jsx', 'r') as f:
    code = f.read()

# Make sure we only add headers if they don't already exist.
def add_headers(m):
    url = m.group(1)
    # Check if there is already an options object
    if m.group(0).endswith(','):
        return m.group(0) # already has args
    
    return f"fetch({url}, {{ headers: {{ 'Authorization': `Bearer ${{token}}` }} }})"

# Just replace all `fetch(URL)` with `fetch(URL, { headers: { 'Authorization': `Bearer ${token}` } })`
new_code = re.sub(r'fetch\(([^,]+)\)(?!\s*\,)', add_headers, code)

with open('C:/PROJECTS/CHASE/frontend/src/App.jsx', 'w') as f:
    f.write(new_code)
print("Updated App.jsx fetches")
