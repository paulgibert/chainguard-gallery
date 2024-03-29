FROM cgr.dev/chainguard/wolfi-base:latest

# Allow statements and log messages to immediately appear in the Cloud Run logs
ENV PYTHONUNBUFFERED True

RUN mkdir /app
WORKDIR /app

RUN apk add python-3.10 py3.10-pip grype

COPY . .
RUN pip install -r requirements.txt
RUN pip install pkg/gryft

ENTRYPOINT gunicorn --bind :${PORT} --timeout ${TIMEOUT} app:app