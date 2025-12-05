# Hyperledger Fabric v2.x Network Setup

Автоматизированная система для развертывания и управления сетью Hyperledger Fabric v2.x с поддержкой external chaincode (Chaincode-as-a-Service).

## Возможности

### ✅ Текущий функционал

1. **Генерация конфигурации сети:**
   - Автоматическая генерация `configtx.yaml` и `crypto-config.yaml`
   - Генерация `docker-compose.yaml` с настройкой всех компонентов
   - Поддержка двух организаций (Org1, Org2) и одного orderer

2. **Генерация криптографических материалов:**
   - Автоматическая генерация сертификатов для всех компонентов
   - Создание genesis блока для ordering service
   - Генерация транзакций создания канала
   - Генерация транзакций anchor peer для обеих организаций

3. **Управление сетью:**
   - Запуск и остановка сети через Docker Compose
   - Просмотр статуса контейнеров
   - Просмотр логов компонентов сети
   - Очистка volumes при остановке

4. **Настройка каналов:**
   - Автоматическое создание канала
   - Присоединение peer'ов к каналу
   - Обновление anchor peer для обеих организаций
   - Поддержка проверки существования канала

5. **Развертывание chaincode:**
   - Создание package для external chaincode (CCAAS)
   - Установка chaincode на peer'ы обеих организаций
   - Одобрение chaincode организациями
   - Коммит chaincode в канал
   - Поддержка chaincode-as-a-service (внешний chaincode)

6. **Chaincode функциональность:**
   - Управление задачами (создание, обновление статуса, получение)
   - Управление версиями документов (добавление версий, получение истории)
   - REST API для взаимодействия с chaincode
   - gRPC сервер для общения с peer'ами

## Требования для запуска

### Обязательные требования

1. **Python 3.7 или выше**
   ```bash
   python --version  # Должно быть 3.7+
   ```

2. **Docker и Docker Compose**
   - Docker версии 20.10 или выше
   - Docker Compose версии 2.0 или выше
   ```bash
   docker --version
   docker compose version
   ```

3. **Python зависимости**
   - Установите зависимости из `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

### Опциональные требования

- **Hyperledger Fabric инструменты** (только для ручной генерации, необязательно)
  - `cryptogen` - для генерации криптографических материалов
  - `configtxgen` - для генерации транзакций канала
  - Вместо этого используется Docker образ `hyperledger/fabric-tools`

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Генерация конфигурации

```bash
python generate_fabric_config.py
```

Это создаст:
- `config/configtx.yaml` - конфигурация для генерации транзакций
- `config/crypto-config.yaml` - конфигурация для криптографических материалов
- `docker-compose.yaml` - конфигурация Docker Compose

### 3. Генерация криптографических материалов и артефактов

```bash
python generate_crypto_materials.py
```

Это создаст:
- `organizations/` - криптографические материалы (сертификаты, ключи)
- `channel-artifacts/genesis.block` - genesis блок для orderer
- `channel-artifacts/npa-channel.tx` - транзакция создания канала
- `channel-artifacts/Org1MSPanchors.tx` - транзакция anchor peer для Org1
- `channel-artifacts/Org2MSPanchors.tx` - транзакция anchor peer для Org2

### 4. Запуск сети

```bash
python network_setup.py start
```

Или напрямую:
```bash
docker compose up -d
```

### 5. Создание и настройка канала

```bash
python channel_setup.py
```

Это выполнит:
- Создание канала `npa-channel`
- Присоединение peer'ов обеих организаций к каналу
- Обновление anchor peer для обеих организаций

### 6. Развертывание chaincode

```bash
cd chaincode
python deploy_chaincode.py
```

Это выполнит:
- Создание package для external chaincode
- Установку chaincode на peer'ы
- Одобрение chaincode организациями
- Коммит chaincode в канал

## Управление сетью

### Статус сети

```bash
python network_setup.py status
```

### Просмотр логов

```bash
python network_setup.py logs
```

### Остановка сети

```bash
python network_setup.py stop
```

### Остановка с очисткой volumes

```bash
python network_setup.py clean
```

## Структура проекта

```
.
├── config/                        # Конфигурационные файлы (генерируется)
│   ├── crypto-config.yaml
│   └── configtx.yaml
├── organizations/                 # Криптографические материалы (генерируется)
│   ├── ordererOrganizations/
│   └── peerOrganizations/
├── channel-artifacts/             # Артефакты канала (генерируется)
│   ├── genesis.block
│   ├── npa-channel.tx
│   └── ...
├── chaincode/                     # Chaincode и инструменты развертывания
│   ├── deploy_chaincode.py       # Скрипт развертывания chaincode
│   ├── npa_chaincode/            # Основной chaincode
│   ├── src/                      # gRPC и REST API серверы
│   └── backend/                  # FastAPI backend
├── generate_fabric_config.py     # Генерация конфигурации
├── generate_crypto_materials.py  # Генерация криптографических материалов
├── channel_setup.py              # Настройка каналов
├── network_setup.py              # Управление сетью
├── docker-compose.yaml           # Docker Compose конфигурация (генерируется)
├── requirements.txt              # Python зависимости
└── README.md                     # Документация
```

## Компоненты сети

- **Fabric CA Orderer**: `ca_orderer` (порт 7054)
- **Fabric CA Org1**: `ca_org1` (порт 7154)
- **Fabric CA Org2**: `ca_org2` (порт 8054)
- **Orderer**: `orderer0` (порт 7050)
- **Org1 Peer**: `peer0.org1.example.com` (порт 7051)
- **Org2 Peer**: `peer0.org2.example.com` (порт 9051)
- **CouchDB для Org1**: `couchdb0` (порт 5984)
- **CouchDB для Org2**: `couchdb1` (порт 5985)

## Chaincode функциональность

### Основные функции

- `createTask` - Создание новой задачи
- `updateTaskStatus` - Обновление статуса задачи
- `addDocumentVersion` - Добавление версии документа к задаче
- `getDocumentVersions` - Получение всех версий документа
- `getTask` - Получение задачи по ID

### REST API

Chaincode предоставляет REST API для удобного взаимодействия:
- `POST /api/v1/tasks` - Создание задачи
- `GET /api/v1/tasks/{task_id}` - Получение задачи
- `PUT /api/v1/tasks/{task_id}/status` - Обновление статуса
- `POST /api/v1/tasks/{task_id}/documents/{doc_id}/versions` - Добавление версии документа
- `GET /api/v1/tasks/{task_id}/documents/{doc_id}/versions` - Получение версий документа

## Особенности

- **Автоматизация**: Все этапы развертывания автоматизированы
- **External Chaincode**: Поддержка chaincode-as-a-service (CCAAS)
- **Docker-based**: Использует Docker для изоляции и удобства развертывания
- **Модульность**: Каждый компонент можно запускать отдельно

## Примечания

- Все конфигурационные файлы генерируются автоматически
- Структура соответствует стандартам Hyperledger Fabric v2.x
- Используется etcdraft как консенсусный алгоритм
- CouchDB используется как state database для обоих peer'ов
- External chaincode работает через gRPC соединение

## Лицензия

[Укажите лицензию, если необходимо]
