FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_DEBUG=0
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "--threads", "4", "--timeout", "300", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
