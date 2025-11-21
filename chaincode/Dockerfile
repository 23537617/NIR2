FROM python:3.10

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Обновление pip до последней версии
RUN pip install --upgrade pip setuptools wheel

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода chaincode
COPY npa_chaincode/ ./npa_chaincode/
COPY src/ ./src/

# Установка переменных окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CHAINCODE_SERVER_PORT=9999
ENV REST_API_PORT=8080
ENV REST_API_HOST=0.0.0.0

# Создание пользователя для запуска chaincode (опционально, для безопасности)
# RUN useradd -m -u 1000 chaincode && chown -R chaincode:chaincode /app
# USER chaincode

# Открытие портов
# 9999 - gRPC сервер для chaincode
# 8080 - REST API (опционально)
EXPOSE 9999 8080

# Команда по умолчанию - запуск chaincode gRPC сервера
# Для REST API используйте: python src/rest_api.py
CMD ["python", "src/grpc_server.py"]

