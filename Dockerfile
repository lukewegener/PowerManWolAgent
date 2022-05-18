# syntax=docker/dockerfile:1

FROM python:3.10-slim-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY ./app .

ENV POLL_INTERVAL=30
ENV STORAGE_ACCOUNT_NAME=
ENV QUEUE_NAME=
ENV AZURE_TENANT_ID=
ENV AZURE_CLIENT_ID=
ENV AZURE_CLIENT_CERTIFICATE_PATH=

CMD [ "python3", "Agent.py"]