FROM python:3.12-slim

ENV TZ=Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime

RUN useradd -m -s /bin/bash jobscout

WORKDIR /app

# Install worker dependencies
COPY worker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Playwright enabled — Hetzner VPS has 4GB RAM (sufficient for Chromium)
RUN playwright install --with-deps chromium

# texlive disabled — ~200MB for PDF generation, not critical for worker loop.
# Re-enable when upgrading plan:
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     texlive-base texlive-latex-extra texlive-fonts-recommended \
#     && rm -rf /var/lib/apt/lists/*

# Copy worker code + templates
COPY worker/ /app/worker/

# Copy job_agent (scrapers reused by worker)
COPY job_agent/ /app/job_agent/

RUN chown -R jobscout:jobscout /app

USER jobscout

CMD ["python", "-m", "worker.main"]
