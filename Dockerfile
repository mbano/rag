FROM python:3.11-slim

ARG APP_USER=appuser
RUN useradd -m -u 1000 ${APP_USER}

WORKDIR /app

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt
ENV NLTK_DATA=/usr/local/share/nltk_data
RUN python -m nltk.downloader -d ${NLTK_DATA} punkt_tab stopwords

COPY app .
COPY /config.yaml /config.yaml

# copy /data and /artifacts as non-root user to make them writable for HF
COPY --chown=${APP_USER}:${APP_USER} /data /data
COPY --chown=${APP_USER}:${APP_USER} /artifacts /artifacts

# tell app where to write data and artifacts
ENV APP_DATA_DIR=/data \
    APP_ARTIFACTS_DIR=/artifacts


USER ${APP_USER}

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
