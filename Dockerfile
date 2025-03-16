# Dockerfile
FROM python:3.9-slim
RUN apt-get update && apt-get install -y gcc libpq-dev
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
# Копируем wait-for-it.sh
COPY wait-for-it.sh /app/
RUN chmod +x /app/wait-for-it.sh
EXPOSE 8000
CMD ["/app/wait-for-it.sh", "db:5432", "--", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
