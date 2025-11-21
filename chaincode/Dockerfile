FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY src/ ./src/

# Установка переменных окружения
ENV PYTHONUNBUFFERED=1
ENV CHAINCODE_SERVER_PORT=9999
ENV REST_API_PORT=8080
ENV REST_API_HOST=0.0.0.0

# Открытие портов
EXPOSE 9999 8080

# Команда по умолчанию - запуск REST API
# Для gRPC используйте: python src/grpc_server.py
CMD ["python", "src/rest_api.py"]

