# -- base --
FROM python:3.11-slim

# Avoid interactive prompts & speed up installs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# App directory
WORKDIR /app

# Use Docker cache: copy manifests first
COPY requirements.txt .

# Install deps (no cache, wheels preferred)
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . /app

# Expose and define the start command
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]

