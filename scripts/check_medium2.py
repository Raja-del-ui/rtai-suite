import json
with open('bandit_report3.json') as f:
    d = json.load(f)
for r in d['results']:
    if r['issue_severity'] == 'MEDIUM':
        print(f'  {r["filename"]}:{r["line_number"]} [{r["test_name"]}]')