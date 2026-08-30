# syntax=docker/dockerfile:1
# Multi-stage build: reproducible deps layer -> slim runtime as non-root user.
FROM python:3.13-slim AS builder
WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY rtai_core ./rtai_core
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RTAI_HOME=/app
WORKDIR /app
COPY --from=builder /install /usr/local
COPY rtai_core ./rtai_core
COPY 01-ai-recon-agent ./01-ai-recon-agent
COPY 02-llm-injection-fuzzer ./02-llm-injection-fuzzer
COPY 03-phishing-awareness-sim ./03-phishing-awareness-sim
COPY 04-c2-detection-lab ./04-c2-detection-lab
COPY 05-pentest-report-copilot ./05-pentest-report-copilot
COPY services ./services
COPY schemas ./schemas
COPY conftest.py ./
COPY LICENSE NOTICE.md EULA.md AUP.md PRIVACY.md DPA.md EXPORT_CONTROL.md TRADEMARK.md TERMS.md ./
COPY packaging/logrotate/rtai-audit /etc/logrotate.d/rtai-audit 2>/dev/null || true
# Military hardening: FIPS check (RHEL UBI would run fips-mode-setup --enable), STIG perms, mTLS cert dir
RUN pip install --no-cache-dir "dnspython>=2.6" "jinja2>=3.1" cryptography \
    && useradd --create-home --shell /bin/bash rtai \
    && mkdir -p /var/log/royal-sec /certs /policies && chown -R rtai:rtai /app /var/log/royal-sec /certs /policies \
    && chmod 750 /var/log/royal-sec && chmod 600 /etc/logrotate.d/rtai-audit 2>/dev/null || true
# Optional FIPS validation at build time (fails open if openssl not FIPS)
RUN python -c "from rtai_core.military_fips import fips_status; print(fips_status())" || true
USER rtai
EXPOSE 8080 9000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:9000/health', timeout=2)" || exit 1
CMD ["python", "services/api/server.py", "--host", "0.0.0.0", "--port", "9000"]
