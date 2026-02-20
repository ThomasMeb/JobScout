FROM python:3.12-slim

# Timezone
ENV TZ=Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime

# Non-root user
RUN useradd -m -s /bin/bash jobscout
WORKDIR /app

# Dependencies (cached layer)
COPY requirements.txt requirements-dashboard.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dashboard.txt

# App code
COPY . .
RUN chown -R jobscout:jobscout /app

USER jobscout

# Data volume
VOLUME ["/app/data"]

# Dashboard port
EXPOSE 8501

# Default: daemon mode
CMD ["python", "-u", "main.py"]
