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
RUN pip install --no-cache-dir "dnspython>=2.6" "jinja2>=3.1" \
    && useradd --create-home --shell /bin/bash rtai \
    && chown -R rtai:rtai /app
USER rtai
EXPOSE 8080 9000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:9000/health', timeout=2)" || exit 1
CMD ["python", "services/api/server.py", "--host", "0.0.0.0", "--port", "9000"]
