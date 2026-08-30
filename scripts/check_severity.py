import json
with open('bandit_report.json') as f:
    d = json.load(f)
for r in d['results']:
    if r['issue_severity'] in ['HIGH', 'CRITICAL']:
        print(f'  {r["filename"]}:{r["line_number"]} [{r["issue_severity"]}] {r["test_name"]}')