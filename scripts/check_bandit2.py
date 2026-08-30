import json
with open('bandit_report2.json') as f:
    d = json.load(f)
print(f'Issues found: {len(d["results"])}')
for r in d['results']:
    if r['issue_severity'] in ['MEDIUM', 'HIGH', 'CRITICAL']:
        print(f'  {r["filename"]}:{r["line_number"]} [{r["issue_severity"]}] {r["test_name"]}')