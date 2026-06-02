FROM python:3.12-slim

ENV TZ=Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime

RUN useradd -m -s /bin/bash jobscout

WORKDIR /app

# Install worker dependencies
COPY worker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Playwright enabled — OVH VPS has sufficient RAM for Chromium.
# IMPORTANT: install browsers into a shared, world-readable path. `playwright install`
# runs as root here (before USER jobscout); the default cache (/root/.cache) is NOT
# readable by the runtime `jobscout` user, which made BrowserType.launch fail with
# "Executable doesn't exist" -> the Playwright Node driver crashed (EPIPE) -> the worker
# process died mid-scrape and was restarted in a loop. PLAYWRIGHT_BROWSERS_PATH is an ENV
# so it persists at runtime; chmod makes the binaries readable by jobscout.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install --with-deps chromium \
    && chmod -R a+rX /ms-playwright

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
