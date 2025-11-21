# TaskDocument Chaincode

Python external chaincode для Hyperledger Fabric, реализующий функции управления задачами и версиями документов.

## Функции

- **createTask** - Создание новой задачи
- **updateTaskStatus** - Обновление статуса задачи
- **addDocumentVersion** - Добавление версии документа к задаче
- **getDocumentVersions** - Получение всех версий документа

## Структура проекта

```
chaincode/
├── src/
│   ├── chaincode.py      # Основная логика chaincode
│   ├── grpc_server.py    # gRPC сервер для общения с peer
│   ├── rest_api.py       # REST API сервер
│   └── __init__.py
├── Dockerfile
├── docker-compose.chaincode.yaml
├── requirements.txt
├── deploy_chaincode.py
└── README.md
```

## Установка

```bash
cd chaincode
pip install -r requirements.txt
```

## Использование

### REST API

Запуск REST API сервера:

```bash
python src/rest_api.py
```

Или через Docker:

```bash
docker-compose -f docker-compose.chaincode.yaml up chaincode-rest
```

REST API будет доступен на `http://localhost:8080`

### gRPC сервер

Запуск gRPC сервера:

```bash
python src/grpc_server.py
```

Или через Docker:

```bash
docker-compose -f docker-compose.chaincode.yaml up chaincode-grpc
```

gRPC сервер будет доступен на порту `9999`

## API Endpoints

### REST API

#### Создать задачу
```bash
POST /api/v1/tasks
Content-Type: application/json

{
  "task_id": "TASK001",
  "title": "Новая задача",
  "description": "Описание задачи",
  "assignee": "user1",
  "creator": "admin"
}
```

#### Получить задачу
```bash
GET /api/v1/tasks/{task_id}
```

#### Обновить статус задачи
```bash
PUT /api/v1/tasks/{task_id}/status
Content-Type: application/json

{
  "status": "IN_PROGRESS",
  "updated_by": "user1"
}
```

#### Добавить версию документа
```bash
POST /api/v1/tasks/{task_id}/documents/{document_id}/versions
Content-Type: application/json

{
  "version": "1.0",
  "content_hash": "abc123...",
  "uploaded_by": "user1",
  "metadata": {
    "filename": "document.pdf",
    "size": 1024
  }
}
```

#### Получить версии документа
```bash
GET /api/v1/tasks/{task_id}/documents/{document_id}/versions
```

### Chaincode функции

#### createTask
```bash
peer chaincode invoke \
  -o orderer0:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --tls \
  --cafile /path/to/orderer-ca.pem \
  -C npa-channel \
  -n taskdocument \
  -c '{"function":"createTask","Args":["TASK001","Новая задача","Описание","user1","admin"]}'
```

#### updateTaskStatus
```bash
peer chaincode invoke \
  -o orderer0:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --tls \
  --cafile /path/to/orderer-ca.pem \
  -C npa-channel \
  -n taskdocument \
  -c '{"function":"updateTaskStatus","Args":["TASK001","IN_PROGRESS","user1"]}'
```

#### addDocumentVersion
```bash
peer chaincode invoke \
  -o orderer0:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --tls \
  --cafile /path/to/orderer-ca.pem \
  -C npa-channel \
  -n taskdocument \
  -c '{"function":"addDocumentVersion","Args":["TASK001","DOC001","1.0","abc123","user1","{}"]}'
```

#### getDocumentVersions
```bash
peer chaincode query \
  -C npa-channel \
  -n taskdocument \
  -c '{"function":"getDocumentVersions","Args":["TASK001","DOC001"]}'
```

## Развертывание в Fabric

### 1. Запуск chaincode сервиса

```bash
# Запуск через docker-compose
docker-compose -f docker-compose.chaincode.yaml up -d chaincode-rest

# Или сборка и запуск вручную
docker build -t taskdocument-chaincode .
docker run -d --name chaincode-rest \
  --network fabric-network \
  -p 8080:8080 -p 9999:9999 \
  taskdocument-chaincode
```

### 2. Установка chaincode на peer'ы

```bash
# Установка на peer0.org1
export CORE_PEER_LOCALMSPID=Org1MSP
export CORE_PEER_ADDRESS=localhost:7051
export CORE_PEER_TLS_ROOTCERT_FILE=./organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=./organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp

peer lifecycle chaincode package taskdocument.tar.gz \
  --path . \
  --lang external \
  --label taskdocument_1.0

peer lifecycle chaincode install taskdocument.tar.gz

# Получить package ID
peer lifecycle chaincode queryinstalled
```

### 3. Одобрение chaincode организациями

```bash
# Org1
export PACKAGE_ID=<package_id_from_previous_step>

peer lifecycle chaincode approveformyorg \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --channelID npa-channel \
  --name taskdocument \
  --version 1.0 \
  --package-id $PACKAGE_ID \
  --sequence 1 \
  --tls \
  --cafile ./organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  --peerAddresses localhost:7051 \
  --tlsRootCertFiles ./organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt

# Org2
export CORE_PEER_LOCALMSPID=Org2MSP
export CORE_PEER_ADDRESS=localhost:9051
export CORE_PEER_TLS_ROOTCERT_FILE=./organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=./organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp

peer lifecycle chaincode approveformyorg \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --channelID npa-channel \
  --name taskdocument \
  --version 1.0 \
  --package-id $PACKAGE_ID \
  --sequence 1 \
  --tls \
  --cafile ./organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  --peerAddresses localhost:9051 \
  --tlsRootCertFiles ./organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
```

### 4. Коммит chaincode в канал

```bash
peer lifecycle chaincode commit \
  -o localhost:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --channelID npa-channel \
  --name taskdocument \
  --version 1.0 \
  --sequence 1 \
  --tls \
  --cafile ./organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem \
  --peerAddresses localhost:7051 \
  --peerAddresses localhost:9051 \
  --tlsRootCertFiles ./organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
  --tlsRootCertFiles ./organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
```

## Примечания

- Для production использования необходимо реализовать полноценный gRPC сервер с использованием protobuf определений из Hyperledger Fabric
- REST API является упрощенной оберткой для тестирования и разработки
- В production рекомендуется использовать только gRPC интерфейс для общения с peer
- Текущая реализация использует упрощенную заглушку для работы с ledger (в памяти). Для production нужно реализовать реальное взаимодействие с peer через gRPC

