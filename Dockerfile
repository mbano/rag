FROM python:3.11-slim

ARG INCLUDE_LOCAL_DATA=true
ARG APP_USER=appuser

# Create non-root user
RUN useradd -m -u 1000 ${APP_USER}

WORKDIR /app

# Install deps
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Download nltk data
ENV NLTK_DATA=/usr/local/share/nltk_data
RUN python -m nltk.downloader -d ${NLTK_DATA} punkt_tab stopwords

# Copy core app and config
COPY app .
COPY /config.yaml /config.yaml

# Always create empty dirs first
RUN mkdir -p /data /artifacts && chown -R ${APP_USER}:${APP_USER} /data /artifacts

# Conditionally copy local data
# If INCLUDE_LOCAL_DATA=true, copy real data; otherwise, leave empty dirs
RUN if [ "$INCLUDE_LOCAL_DATA" = "true" ]; then \
        echo "Including local data..."; \
        cp -r /app/data /data 2>/dev/null || true; \
        cp -r /app/artifacts /artifacts 2>/dev/null || true; \
    else \
        echo "Skipping local data (will be downloaded at runtime)..."; \
    fi

# Tell app where to write data
ENV APP_DATA_DIR=/data \
    APP_ARTIFACTS_DIR=/artifacts

USER ${APP_USER}

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
