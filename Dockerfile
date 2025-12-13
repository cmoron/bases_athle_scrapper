# Multi-stage Dockerfile for mypacer_scraper
# Supports both development and production environments

# =============================================================================
# Stage 'base': Common dependencies
# =============================================================================
FROM python:3.12-slim AS base

# Avoids writing .pyc files and enables unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (production only)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 'dev': Development environment
# =============================================================================
FROM base AS dev

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy only necessary files and directories
COPY --chown=appuser:appuser core/ ./core/
COPY --chown=appuser:appuser scraper/ ./scraper/
COPY --chown=appuser:appuser tools/ ./tools/
COPY --chown=appuser:appuser populate_database.sh update_database.sh ./
COPY --chown=appuser:appuser crontab ./crontab

# Remove write permissions and make scripts executable (read-only + execute)
RUN chmod -R a-w /app && \
    chmod 555 populate_database.sh update_database.sh

# Switch to non-root user
USER appuser

# Keep container running for manual interaction
# Use: docker-compose exec scraper bash
CMD ["tail", "-f", "/dev/null"]

# =============================================================================
# Stage 'prod': Production environment with Supercronic
# =============================================================================
FROM base AS prod

# Install Supercronic (cron for containers)
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.29/supercronic-linux-amd64 \
    SUPERCRONIC=supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=cd48d45c4b10f3f0bfdd3a57d054cd05ac96812b

RUN wget -q "$SUPERCRONIC_URL" \
    && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
    && chmod +x "$SUPERCRONIC" \
    && mv "$SUPERCRONIC" /usr/local/bin/supercronic

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy only necessary files and directories
COPY --chown=appuser:appuser core/ ./core/
COPY --chown=appuser:appuser scraper/ ./scraper/
COPY --chown=appuser:appuser tools/ ./tools/
COPY --chown=appuser:appuser populate_database.sh update_database.sh ./
COPY --chown=appuser:appuser crontab ./crontab

# Remove write permissions and make scripts executable (read-only + execute)
RUN chmod -R a-w /app && \
    chmod 555 populate_database.sh update_database.sh

# Switch to non-root user
USER appuser

# Run Supercronic with crontab
# This will keep the container running and execute scheduled tasks
CMD ["supercronic", "/app/crontab"]
