# syntax=docker/dockerfile:1

FROM python:3.11-slim

# System deps: git is needed by some HF model repos that use git-based
# revisions; build-essential covers packages that need to compile.
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Cache HF downloads inside the container's writable layer so repeated
# cold starts on the same instance don't re-download the models.
ENV HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    PYTHONUNBUFFERED=1

# Cloud Run injects $PORT (defaults to 8080); Streamlit must bind to it
# and to 0.0.0.0, not localhost.
ENV PORT=8080
EXPOSE 8080

# Basic container healthcheck (Streamlit exposes this endpoint natively)
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s \
    CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\",8080)}/_stcore/health')" || exit 1

CMD streamlit run app.py \
    --server.port=${PORT} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.gatherUsageStats=false
