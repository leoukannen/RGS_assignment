FROM python:3.12-slim

WORKDIR /app

COPY python-docker-src/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY python-docker-src/ .

CMD ["python", "src/main.py"]