FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y wkhtmltopdf && \
    apt-get clean

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD ["python", "-u", "app.py"]