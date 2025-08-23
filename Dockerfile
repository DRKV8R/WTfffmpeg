FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# The fix: This line explicitly tells Gunicorn to load the 'app' object from 'app.py'
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
