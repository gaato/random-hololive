FROM python:3.11-bullseye

COPY src/ /app
WORKDIR /app

RUN apt update && apt install -y cron

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "main.py"]
