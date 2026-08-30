import pathlib

content = pathlib.Path('BOOK.md').read_text(encoding='utf-8')

# 1. Add HTML/Docker to Platform API section
old_platform = '''### Security

- **Bearer auth** when `RTAI_API_TOKEN` set
- **Rate limiting** - 60 req/min per IP (sliding window)
- **Security headers** - nosniff, DENY, no-store, no-referrer
- **Active recon** requires `X-RTAI-Authorized: yes` header'''

new_platform = '''### Security

- **Bearer auth** when `RTAI_API_TOKEN` set
- **Rate limiting** - 60 req/min per IP (sliding window)
- **Security headers** - nosniff, DENY, no-store, no-referrer
- **Active recon** requires `X-RTAI-Authorized: yes` header

### Output Formats

| Format | Command | Description |
|--------|---------|-------------|
| JSON | `POST /v1/recon` | Machine-readable findings bundle |
| HTML | `copilot.py --format html` | Styled client report with severity badges |
| SARIF | `--junit` / `--sarif` | CI/CD integration |

### Container Deployment

```bash
# Build image
docker build -t rtai-suite .

# Run API server
docker run -p 9000:9000 -e RTAI_API_TOKEN=$TOKEN rtai-suite

# Or with docker-compose
docker compose up api
```

### Observability

| Endpoint | Format | Purpose |
|----------|--------|---------|
| `/metrics` | Prometheus text | Scraping / alerting |
| `/health` | JSON | Liveness/readiness |
| `/openapi.json` | JSON | API contract |'''

content = content.replace(
    '### Security\n\n- **Bearer auth** when `RTAI_API_TOKEN` set\n- **Rate limiting** - 60 req/min per IP (sliding window)\n- **Security headers** - nosniff, DENY, no-store, no-referrer\n- **Active recon** requires `X-RTAI-Authorized: yes` header',
    '''### Security

- **Bearer auth** when `RTAI_API_TOKEN` set
- **Rate limiting** - 60 req/min per IP (sliding window)
- **Security headers** - nosniff, DENY, no-store, no-referrer
- **Active recon** requires `X-RTAI-Authorized: yes` header

### Output Formats

| Format | Command | Description |
|--------|---------|-------------|
| JSON | `POST /v1/recon` | Machine-readable findings bundle |
| HTML | `copilot.py --format html` | Styled client report with severity badges |
| SARIF | `--junit` / `--sarif` | CI/CD integration |

### Container Deployment

```bash
# Build image
docker build -t rtai-suite .

# Run API server
docker run -p 9000:9000 -e RTAI_API_TOKEN=$TOKEN rtai-suite

# Or with docker-compose
docker compose up api
```

### Observability

| Endpoint | Format | Purpose |
|----------|--------|---------|
| `/metrics` | Prometheus text | Scraping / alerting |
| `/health` | JSON | Liveness/readiness |
| `/openapi.json` | JSON | API contract |''')

# 2. Update Architecture section with Docker
old_arch = """### Suite Architecture

```
                 ┌────────────────────────────────────────────────────────────┐
                 │        shared llm_client.py (stdlib only)                  │
                 │   OpenAI ─│─ Anthropic ─│─ Ollama(local/free)              │
                 └──────┬──────────┬──────────┬─────────┬────────────────────┘
                        │          │          │         │
   P1 recon-agent ──────┘   P2 fuzzer    P3 phish-sim  P5 report-copilot
   RDAP·DNS·CT·TLS          payloads→    templates→    nmap/nuclei/Nessus
   Wayback·HTTP             ↖ judge ↗    →landing.py    →correlate→narrate
   →score→diff              ↖ beacon ↖   →metrics       →roadmap→report.md
                                  P4 c2-lab (offline): listener ⇄ beacon
                                  presets·schedule·kill-switch → analyze → Sigma
```"""

new_arch = """### Suite Architecture

```
                 ┌────────────────────────────────────────────────────────────┐
                 │        shared llm_client.py (stdlib only)                  │
                 │   OpenAI ─│─ Anthropic ─│─ Ollama(local/free)              │
                 └──────┬──────────┬──────────┬─────────┬────────────────────┘
                        │          │          │         │
   P1 recon-agent ──────┘   P2 fuzzer    P3 phish-sim  P5 report-copilot
   RDAP·DNS·CT·TLS          payloads→    templates→    nmap/nuclei/Nessus
   Wayback·HTTP             ↖ judge ↗    →landing.py    →correlate→narrate
   →score→diff              ↖ beacon ↖   →metrics       →roadmap→report.md
                                  P4 c2-lab (offline): listener ⇄ beacon
                                  presets·schedule·kill-switch → analyze → Sigma
```

**Container Deployment**

```dockerfile
# Multi-stage build (see Dockerfile)
FROM python:3.13-slim AS builder
# ... build stage ...

FROM python:3.13-slim AS runtime
USER 1000:1000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9000/health', timeout=2)" || exit 1
CMD ["python", "services/api/server.py", "--host", "0.0.0.0", "--port", "9000"]
```

```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports:
      - "9000:9000"
    environment:
      - RTAI_API_TOKEN=${RTAI_API_TOKEN}
    restart: unless-stopped
```

```bash
# Run
docker compose up api
```

**Observability**

| Endpoint | Format | Purpose |
|----------|--------|---------|
| `/metrics` | Prometheus text | Scraping / alerting |
| `/health` | JSON | Liveness/readiness |
| `/openapi.json` | JSON | API contract |"""

# Apply changes
import pathlib
content = pathlib.Path('BOOK.md').read_text(encoding='utf-8')

# Update Platform API section
old_platform = """### Security

- **Bearer auth** when `RTAI_API_TOKEN` set
- **Rate limiting** - 60 req/min per IP (sliding window)
- **Security headers** - nosniff, DENY, no-store, no-referrer
- **Active recon** requires `X-RTAI-Authorized: yes` header"""

new_platform = """### Security

- **Bearer auth** when `RTAI_API_TOKEN` set
- **Rate limiting** - 60 req/min per IP (sliding window)
- **Security headers** - nosniff, DENY, no-store, no-referrer
- **Active recon** requires `X-RTAI-Authorized: yes` header

### Output Formats

| Format | Command | Description |
|--------|---------|-------------|
| JSON | `POST /v1/recon` | Machine-readable findings bundle |
| HTML | `copilot.py --format html` | Styled client report with severity badges |
| SARIF | `--junit` / `--sarif` | CI/CD integration |

### Container Deployment

```bash
# Build image
docker build -t rtai-suite .

# Run API server
docker run -p 9000:9000 -e RTAI_API_TOKEN=$TOKEN rtai-suite

# Or with docker-compose
docker compose up api
```

### Observability

| Endpoint | Format | Purpose |
|----------|--------|---------|
| `/metrics` | Prometheus text | Scraping / alerting |
| `/health` | JSON | Liveness/readiness |
| `/openapi.json` | JSON | API contract |"""

content = content.replace(
    "### Security\n\n- **Bearer auth** when `RTAI_API_TOKEN` set\n- **Rate limiting** - 60 req/min per IP (sliding window)\n- **Security headers** - nosniff, DENY, no-store, no-referrer\n- **Active recon** requires `X-RTAI-Authorized: yes` header",
    new_platform
)

# Update Architecture section
old_arch = """### Suite Architecture

```
                 ┌────────────────────────────────────────────────────────────┐
                 │        shared llm_client.py (stdlib only)                  │
                 │   OpenAI ─│─ Anthropic ─│─ Ollama(local/free)              │
                 └──────┬──────────┬──────────┬─────────┬────────────────────┘
                        │          │          │         │
   P1 recon-agent ──────┘   P2 fuzzer    P3 phish-sim  P5 report-copilot
   RDAP·DNS·CT·TLS          payloads→    templates→    nmap/nuclei/Nessus
   Wayback·HTTP             ↖ judge ↗    →landing.py    →correlate→narrate
   →score→diff              ↖ beacon ↖   →metrics       →roadmap→report.md
                                  P4 c2-lab (offline): listener ⇄ beacon
                                  presets·schedule·kill-switch → analyze → Sigma
```"""

new_arch = """### Suite Architecture

```
                 ┌────────────────────────────────────────────────────────────┐
                 │        shared llm_client.py (stdlib only)                  │
                 │   OpenAI ─│─ Anthropic ─│─ Ollama(local/free)              │
                 └──────┬──────────┬──────────┬─────────┬────────────────────┘
                        │          │          │         │
   P1 recon-agent ──────┘   P2 fuzzer    P3 phish-sim  P5 report-copilot
   RDAP·DNS·CT·TLS          payloads→    templates→    nmap/nuclei/Nessus
   Wayback·HTTP             ↖ judge ↗    →landing.py    →correlate→narrate
   →score→diff              ↖ beacon ↖   →metrics       →roadmap→report.md
                                  P4 c2-lab (offline): listener ⇄ beacon
                                  presets·schedule·kill-switch → analyze → Sigma
```

**Container Deployment**

```dockerfile
# Multi-stage build (see Dockerfile)
FROM python:3.13-slim AS builder
# ... build stage ...

FROM python:3.13-slim AS runtime
USER 1000:1000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9000/health', timeout=2)" || exit 1
CMD ["python", "services/api/server.py", "--host", "0.0.0.0", "--port", "9000"]
```

```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports:
      - "9000:9000"
    environment:
      - RTAI_API_TOKEN=${RTAI_API_TOKEN}
    restart: unless-stopped
```

```bash
# Run
docker compose up api
```

**Observability**

| Endpoint | Format | Purpose |
|----------|--------|---------|
| `/metrics` | Prometheus text | Scraping / alerting |
| `/health` | JSON | Liveness/readiness |
| `/openapi.json` | JSON | API contract |"""

content = content.replace(
    """### Suite Architecture

```
                 ┌────────────────────────────────────────────────────────────┐
                 │        shared llm_client.py (stdlib only)                  │
                 │   OpenAI ─│─ Anthropic ─│─ Ollama(local/free)              │
                 └──────┬──────────┬──────────┬─────────┬────────────────────┘
                        │          │          │         │
   P1 recon-agent ──────┘   P2 fuzzer    P3 phish-sim  P5 report-copilot
   RDAP·DNS·CT·TLS          payloads→    templates→    nmap/nuclei/Nessus
   Wayback·HTTP             ↖ judge ↗    →landing.py    →correlate→narrate
   →score→diff              ↖ beacon ↖   →metrics       →roadmap→report.md
                                  P4 c2-lab (offline): listener ⇄ beacon
                                  presets·schedule·kill-switch → analyze → Sigma
```""",
    new_arch
)

# Also update P5 section for HTML output
old_p5 = """### 5. Pentest Report Copilot

**Purpose:** AI-assisted professional pentest report generation.

```bash
# Skeleton report (no LLM)
python copilot.py --nmap scan.xml --company "Acme Corp" --no-llm
python copilot.py --nmap scan.xml --nuclei findings.jsonl --company "Acme" --assessment-type "External Network Penetration Test"
```"""

new_p5 = """### 5. Pentest Report Copilot

**Purpose:** AI-assisted professional pentest report generation.

```bash
# Skeleton report (no LLM)
python copilot.py --nmap scan.xml --company "Acme Corp" --no-llm --out report.md

# Full AI report
python copilot.py --nmap scan.xml --nuclei findings.jsonl --company "Acme Corp" \\
  --assessment-type "External Network Penetration Test"

# Export formats
python copilot.py --nmap scan.xml --format html --out report.html   # HTML report
python copilot.py --nmap scan.xml --format json --out findings.json  # JSON bundle
python copilot.py --nmap scan.xml --format markdown --out report.md  # Markdown (default)
```

**Output Formats:**

| Format | Flag | Description |
|--------|------|-------------|
| Markdown | `--format markdown` | Human-readable, git-friendly |
| HTML | `--format html` | Styled report with severity badges, cards |
| JSON | `--format json` | Machine-readable, CI/CD ready |
| SARIF | `--format sarif` | Static analysis results interchange format |

**HTML Output Example:**
```bash
python copilot.py --nmap scan.xml --format html --out report.html
# Generates styled report with severity badges, finding cards, and a printable executive summary
```"""

# Apply all changes
import pathlib
content = pathlib.Path('BOOK.md').read_text(encoding='utf-8')

# Replace Platform API section
content = content.replace(
    """### Security

- **Bearer auth** when `RTAI_API_TOKEN` set
- **Rate limiting** - 60 req/min per IP (sliding window)
- **Security headers** - nosniff, DENY, no-store, no-referrer
- **Active recon** requires `X-RTAI-Authorized: yes` header""",
    """### Security

- **Bearer auth** when `RTAI_API_TOKEN` set
- **Rate limiting** - 60 req/min per IP (sliding window)
- **Security headers** - nosniff, DENY, no-store, no-referrer
- **Active recon** requires `X-RTAI-Authorized: yes` header

### Output Formats

| Format | Command | Description |
|--------|---------|-------------|
| JSON | `POST /v1/recon` | Machine-readable findings bundle |
| HTML | `copilot.py --format html` | Styled client report with severity badges |
| SARIF | `--junit` / `--sarif` | CI/CD integration |

### Container Deployment

```bash
# Build image
docker build -t rtai-suite .

# Run API server
docker run -p 9000:9000 -e RTAI_API_TOKEN=$TOKEN rtai-suite

# Or with docker-compose
docker compose up api
```

### Observability

| Endpoint | Format | Purpose |
|----------|--------|---------|
| `/metrics` | Prometheus text | Scraping / alerting |
| `/health` | JSON | Liveness/readiness |
| `/openapi.json` | JSON | API contract |"""
)

# Update Architecture section
content = content.replace(
    """### Suite Architecture

```
                 ┌────────────────────────────────────────────────────────────┐
                 │        shared llm_client.py (stdlib only)                  │
                 │   OpenAI ─│─ Anthropic ─│─ Ollama(local/free)              │
                 └──────┬──────────┬──────────┬─────────┬────────────────────┘
                        │          │          │         │
   P1 recon-agent ──────┘   P2 fuzzer    P3 phish-sim  P5 report-copilot
   RDAP·DNS·CT·TLS          payloads→    templates→    nmap/nuclei/Nessus
   Wayback·HTTP             ↖ judge ↗    →landing.py    →correlate→narrate
   →score→diff              ↖ beacon ↖   →metrics       →roadmap→report.md
                                  P4 c2-lab (offline): listener ⇄ beacon
                                  presets·schedule·kill-switch → analyze → Sigma
```""",
    """### Suite Architecture

```
                 ┌────────────────────────────────────────────────────────────┐
                 │        shared llm_client.py (stdlib only)                  │
                 │   OpenAI ─│─ Anthropic ─│─ Ollama(local/free)              │
                 └──────┬──────────┬──────────┬─────────┬────────────────────┘
                        │          │          │         │
   P1 recon-agent ──────┘   P2 fuzzer    P3 phish-sim  P5 report-copilot
   RDAP·DNS·CT·TLS          payloads→    templates→    nmap/nuclei/Nessus
   Wayback·HTTP             ↖ judge ↗    →landing.py    →correlate→narrate
   →score→diff              ↖ beacon ↖   →metrics       →roadmap→report.md
                                  P4 c2-lab (offline): listener ⇄ beacon
                                  presets·schedule·kill-switch → analyze → Sigma
```

**Container Deployment**

```dockerfile
# Multi-stage build (see Dockerfile)
FROM python:3.13-slim AS builder
# ... build stage ...

FROM python:3.13-slim AS runtime
USER 1000:1000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9000/health', timeout=2)" || exit 1
CMD ["python", "services/api/server.py", "--host", "0.0.0.0", "--port", "9000"]
```

```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports:
      - "9000:9000"
    environment:
      - RTAI_API_TOKEN=${RTAI_API_TOKEN}
    restart: unless-stopped
```

```bash
# Run
docker compose up api
```

**Observability**

| Endpoint | Format | Purpose |
|----------|--------|---------|
| `/metrics` | Prometheus text | Scraping / alerting |
| `/health` | JSON | Liveness/readiness |
| `/openapi.json` | JSON | API contract |"""
)

pathlib.Path('BOOK.md').write_text(content, encoding='utf-8')
print('Updated BOOK.md with HTML/Docker references')
print('Done!')