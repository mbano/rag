FROM python:3.11-slim

ARG INCLUDE_LOCAL_DATA=false
ARG APP_USER=appuser

# Create non-root user
RUN useradd -m -u 1000 ${APP_USER}

WORKDIR /

# Install deps
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Download nltk data
ENV NLTK_DATA=/usr/local/share/nltk_data
RUN python -m nltk.downloader -d ${NLTK_DATA} punkt_tab stopwords

# Copy core app and config
COPY /app /app
COPY /config.yaml /config.yaml

# Always create empty dirs first
RUN mkdir -p /data /artifacts && chown -R ${APP_USER}:${APP_USER} /data /artifacts

# Copy local data into temporary build locations
COPY ./data /tmp_data
COPY ./artifacts /tmp_artifacts

# Conditionally move them into place
ARG INCLUDE_LOCAL_DATA=false
RUN if [ "$INCLUDE_LOCAL_DATA" = "true" ]; then \
        echo "Including local data..."; \
        cp -r /tmp_data/. /data/; \
        cp -r /tmp_artifacts/. /artifacts/; \
    else \
        echo "Skipping local data (will be downloaded at runtime)..."; \
    fi && \
    rm -rf /tmp_data /tmp_artifacts

# Tell app where to write data
ENV APP_DATA_DIR=/data \
    APP_ARTIFACTS_DIR=/artifacts

USER ${APP_USER}

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
