FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py database.py mentions.py main.py ./
COPY handlers/ handlers/

CMD ["python", "-u", "main.py"]
