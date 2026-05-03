FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY trading_system/requirements.txt trading_system/requirements.txt
COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir \
    -r trading_system/requirements.txt \
    -r api/requirements.txt

# Copy source
COPY trading_system/ trading_system/
COPY api/ api/

# Create data directory for SQLite DB
RUN mkdir -p trading_system/data logs

EXPOSE 8000

# Default command: run the API
# Override in docker-compose for the bot service
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
