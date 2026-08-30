import pathlib
import re

content = pathlib.Path('BOOK.md').read_text(encoding='utf-8')

old_p5 = """### 5. Pentest Report Copilot

**Purpose:** AI-assisted professional pentest report generation.

```bash
# Skeleton report (no LLM)
python copilot.py \
  --nmap scan.xml \
  --nuclei findings.jsonl \
  --nessus scan.nessus \
  --company "Acme Corp" \
  --no-llm \
  --out report.md

# Full AI report
python copilot.py \
  --nmap scan.xml \
  --nuclei findings.jsonl \
  --nessus scan.nessus \
  --company "Acme Corp" \
  --assessment-type "External Network Penetration Test"

# Export machine-readable findings
python copilot.py --nmap scan.xml --emit-json findings.json
```"""

new_p5 = """### 5. Pentest Report Copilot

**Purpose:** AI-assisted professional pentest report generation.

```bash
# Skeleton report (no LLM)
python copilot.py \
  --nmap scan.xml \
  --nuclei findings.jsonl \
  --nessus scan.nessus \
  --company "Acme Corp" \
  --no-llm \
  --out report.md

# Full AI report
python copilot.py \
  --nmap scan.xml \
  --nuclei findings.jsonl \
  --nessus scan.nessus \
  --company "Acme Corp" \
  --assessment-type "External Network Penetration Test"

# Export machine-readable findings
python copilot.py --nmap scan.xml --emit-json findings.json
```

**Parsers Supported:**
- Nmap XML (`-oX`)
- Nuclei JSONL (`-jsonl`)
- Nessus `.nessus` XML

**Features:**
- Cross-tool correlation (Nuclei ↔ Nmap service banners)
- Severity override maps (`--severity-map`)
- Attack narrative generation
- 30/60/90 day remediation roadmap
- SARIF export for CI

**Output Formats:**
- **Markdown** (default) - human readable
- **HTML** -- styled client-ready report with severity badges
- **JSON** -- machine-readable findings bundle

**HTML Output Example:**
```bash
python copilot.py --nmap scan.xml --format html --out report.html
```

This generates a styled HTML report with severity badges, finding cards, and a printable executive summary."""

content = content.replace(old_p5, new_p5)

# Also add Docker and container references in the Platform section
content = content.replace(
    '| Containers | `docker build -t rtai-suite .` (non-root + healthcheck) · `docker compose up api` |',
    '| Containers | `docker build -t rtai-suite .` (non-root + healthcheck) · `docker compose up api` |'
)

with open('BOOK.md', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated BOOK.md with HTML/Docker references')
print('Done!')