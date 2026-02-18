FROM python:3.12-slim

ENV TZ=Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime

RUN useradd -m -s /bin/bash jobscout
WORKDIR /app

# Install worker dependencies
COPY worker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY worker/ /app/worker/

# Copy job_agent (scrapers reused by worker)
COPY job_agent/ /app/job_agent/

RUN chown -R jobscout:jobscout /app

USER jobscout

CMD ["python", "-m", "worker.main"]
