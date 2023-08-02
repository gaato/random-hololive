FROM python:3.11-bullseye

COPY src/ /app
WORKDIR /app

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "main.py"]
