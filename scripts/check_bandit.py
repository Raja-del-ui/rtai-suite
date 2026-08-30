import json
with open('bandit_report.json') as f:
    data = json.load(f)
print(f'Issues found: {len(data["results"])}')
for r in data['results'][:20]:
    print(f'  {r["filename"]}:{r["line_number"]} [{r["issue_severity"]}] {r["test_name"]}')