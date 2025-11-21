# Быстрый старт

## Локальный запуск

### 1. Установка зависимостей

```bash
cd chaincode
pip install -r requirements.txt
```

### 2. Запуск REST API

```bash
python src/rest_api.py
```

API будет доступен на `http://localhost:8080`

### 3. Тестирование API

В другом терминале:

```bash
python test_api.py
```

## Docker запуск

### 1. Сборка образа

```bash
docker build -t taskdocument-chaincode .
```

### 2. Запуск через docker-compose

```bash
docker-compose -f docker-compose.chaincode.yaml up -d chaincode-rest
```

### 3. Проверка работы

```bash
curl http://localhost:8080/health
```

## Примеры использования

### Создание задачи

```bash
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "TASK001",
    "title": "Новая задача",
    "description": "Описание задачи",
    "assignee": "user1",
    "creator": "admin"
  }'
```

### Получение задачи

```bash
curl http://localhost:8080/api/v1/tasks/TASK001
```

### Обновление статуса

```bash
curl -X PUT http://localhost:8080/api/v1/tasks/TASK001/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "IN_PROGRESS",
    "updated_by": "user1"
  }'
```

### Добавление версии документа

```bash
curl -X POST http://localhost:8080/api/v1/tasks/TASK001/documents/DOC001/versions \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0",
    "content_hash": "abc123",
    "uploaded_by": "user1",
    "metadata": {
      "filename": "document.pdf",
      "size": 1024
    }
  }'
```

### Получение версий документа

```bash
curl http://localhost:8080/api/v1/tasks/TASK001/documents/DOC001/versions
```

