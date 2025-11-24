# Docker Compose - Полная конфигурация

Этот `docker-compose.yaml` объединяет все компоненты системы:

- **Hyperledger Fabric Network** (Orderer, Peers, CA, CouchDB)
- **Python Chaincode** (gRPC сервер)
- **FastAPI Backend** (REST API)
- **IPFS Daemon** (децентрализованное хранилище)

## Быстрый старт

### Предварительные требования

1. Docker и Docker Compose установлены
2. Сгенерированы криптографические материалы и каналы:
   ```bash
   python generate_crypto_materials.py
   python channel_setup.py
   ```

### Запуск всех сервисов

```bash
docker compose up -d
```

### Проверка статуса

```bash
docker compose ps
```

### Просмотр логов

```bash
# Все сервисы
docker compose logs -f

# Конкретный сервис
docker compose logs -f api
docker compose logs -f chaincode
docker compose logs -f ipfs
```

### Остановка всех сервисов

```bash
docker compose down
```

### Остановка с удалением volumes (⚠️ удалит данные)

```bash
docker compose down -v
```

## Порты сервисов

| Сервис | Порт | Описание |
|--------|------|----------|
| Orderer | 7050 | Orderer gRPC |
| Peer0 Org1 | 7051 | Peer gRPC |
| Peer0 Org2 | 9051 | Peer gRPC |
| CA Orderer | 7054, 9443 | Certificate Authority |
| CA Org1 | 7054, 9444 | Certificate Authority |
| CA Org2 | 8054, 9445 | Certificate Authority |
| CouchDB Org1 | 5984 | State Database |
| CouchDB Org2 | 5985 | State Database |
| Chaincode gRPC | 9999 | Chaincode gRPC сервер |
| Chaincode REST | 8080 | Chaincode REST API (опционально) |
| FastAPI Backend | 8000 | REST API |
| IPFS API | 5001 | IPFS API |
| IPFS Gateway | 8081 | IPFS Gateway |

## Структура сервисов

### 1. Fabric Network

- **ca_orderer** - Certificate Authority для Orderer
- **ca_org1** - Certificate Authority для Org1
- **ca_org2** - Certificate Authority для Org2
- **orderer0** - Ordering Service
- **couchdb0** - State Database для Org1
- **couchdb1** - State Database для Org2
- **peer0.org1.example.com** - Peer для Org1
- **peer0.org2.example.com** - Peer для Org2

### 2. Python Chaincode

Сервис `chaincode` запускает Python chaincode как внешний сервис (Chaincode-as-a-Service).

**Конфигурация:**
- gRPC порт: 9999
- REST API порт: 8080 (опционально)

**Зависимости:**
- Требует запущенные peer'ы

### 3. FastAPI Backend

Сервис `api` предоставляет REST API для взаимодействия с chaincode.

**Переменные окружения:**
- `FABRIC_CONNECTION_PROFILE` - путь к connection profile
- `FABRIC_CHANNEL` - имя канала (по умолчанию: npa-channel)
- `FABRIC_CHAINCODE` - имя chaincode (по умолчанию: taskdocument)
- `IPFS_HOST` - хост IPFS (по умолчанию: ipfs)
- `IPFS_PORT` - порт IPFS API (по умолчанию: 5001)

**Зависимости:**
- Требует запущенные peer'ы, chaincode и IPFS

### 4. IPFS Daemon

Сервис `ipfs` запускает IPFS daemon для децентрализованного хранилища документов.

**Порты:**
- 4001 - Swarm port
- 5001 - API port
- 8081 - Gateway port

## Доступ к сервисам

### FastAPI Backend

```bash
# Проверка здоровья
curl http://localhost:8000/health

# Swagger документация
open http://localhost:8000/docs
```

### IPFS

```bash
# Проверка IPFS
curl http://localhost:5001/api/v0/version

# IPFS Gateway
open http://localhost:8081/ipfs/QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG
```

### Chaincode REST API (если включен)

```bash
curl http://localhost:8080/health
```

## Развертывание Chaincode

После запуска всех сервисов необходимо развернуть chaincode на peers:

```bash
# Используйте скрипт развертывания
python chaincode/deploy_chaincode.py
```

Или вручную через Docker:

```bash
# Войти в контейнер peer
docker exec -it peer0.org1.example.com bash

# Установить и одобрить chaincode
peer lifecycle chaincode package taskdocument.tar.gz --path /opt/gopath/src/github.com/chaincode --lang external --label taskdocument_1.0
peer lifecycle chaincode install taskdocument.tar.gz
# ... и т.д.
```

## Troubleshooting

### Проблема: Сервисы не могут подключиться друг к другу

**Решение:** Убедитесь, что все сервисы находятся в одной Docker сети `fabric-network`.

```bash
docker network inspect fabric-network
```

### Проблема: Chaincode не может подключиться к peer

**Решение:** 
1. Проверьте, что peer запущен: `docker compose ps`
2. Проверьте логи chaincode: `docker compose logs chaincode`
3. Убедитесь, что chaincode правильно настроен в connection profile

### Проблема: FastAPI не может подключиться к Fabric

**Решение:**
1. Проверьте переменные окружения в `docker-compose.yaml`
2. Убедитесь, что connection profile доступен по указанному пути
3. Проверьте логи: `docker compose logs api`

### Проблема: IPFS не запускается

**Решение:**
1. Проверьте, что порты 4001, 5001, 8081 свободны
2. Очистите volumes: `docker compose down -v` (⚠️ удалит данные)
3. Проверьте логи: `docker compose logs ipfs`

## Масштабирование

### Запуск только Fabric сети

Если нужна только Fabric сеть без других сервисов:

```bash
docker compose up -d ca_orderer ca_org1 ca_org2 orderer0 couchdb0 couchdb1 peer0.org1.example.com peer0.org2.example.com
```

### Запуск только Backend и IPFS

Для разработки backend без полной Fabric сети (требует внешнюю Fabric сеть):

```bash
docker compose up -d ipfs api
```

## Обновление образов

```bash
# Пересборка chaincode
docker compose build chaincode

# Пересборка API
docker compose build api

# Перезапуск
docker compose up -d chaincode api
```

## Очистка

```bash
# Остановка и удаление контейнеров
docker compose down

# Остановка, удаление контейнеров и volumes
docker compose down -v

# Остановка, удаление контейнеров, volumes и сетей
docker compose down -v --remove-orphans
```



