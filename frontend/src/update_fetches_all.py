import re
import os

for fname in ['CaseBrowser.jsx', 'Chatbot.jsx', 'PatrolPlanner.jsx']:
    with open(f'C:/PROJECTS/CHASE/frontend/src/{fname}', 'r') as f:
        code = f.read()

    # Just replace all `fetch(URL)` with `fetch(URL, { headers: { 'Authorization': `Bearer ${token}` } })`
    def add_headers(m):
        url = m.group(1)
        if m.group(0).endswith(','):
            return m.group(0) # already has args
        return f"fetch({url}, {{ headers: {{ 'Authorization': `Bearer ${{token}}` }} }})"
    
    new_code = re.sub(r'fetch\(([^,]+)\)(?!\s*\,)', add_headers, code)

    # For fetches that already have an options object (like POST), we need to inject headers.
    def inject_headers_in_options(m):
        url = m.group(1)
        options = m.group(2)
        if "'Authorization'" not in options and '"Authorization"' not in options:
            if 'headers:' in options:
                # Add it to existing headers
                options = re.sub(r'headers:\s*\{', r'headers: { \'Authorization\': `Bearer ${token}`, ', options)
            else:
                # Add headers object
                options = options.replace('{', r'{ headers: { \'Authorization\': `Bearer ${token}` }, ', 1)
        return f"fetch({url}, {options})"

    new_code = re.sub(r'fetch\(([^,]+),\s*(\{.*?})\)', inject_headers_in_options, new_code, flags=re.DOTALL)
    
    # ensure token is in props
    if 'function CaseBrowser({' in new_code and 'token' not in new_code.split('function CaseBrowser({')[1].split('}')[0]:
        new_code = new_code.replace('function CaseBrowser({', 'function CaseBrowser({ token, ')
    if 'function Chatbot({' in new_code and 'token' not in new_code.split('function Chatbot({')[1].split('}')[0]:
        new_code = new_code.replace('function Chatbot({', 'function Chatbot({ token, ')
    if 'function PatrolPlanner({' in new_code and 'token' not in new_code.split('function PatrolPlanner({')[1].split('}')[0]:
        new_code = new_code.replace('function PatrolPlanner({', 'function PatrolPlanner({ token, ')

    with open(f'C:/PROJECTS/CHASE/frontend/src/{fname}', 'w') as f:
        f.write(new_code)
print("Updated other components")
