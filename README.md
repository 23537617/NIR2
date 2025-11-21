# Hyperledger Fabric v2.x Минимальная Конфигурация

Минимальная конфигурация Hyperledger Fabric v2.x с двумя организациями (Org1, Org2) и одним каналом `npa-channel`.

## Быстрый старт

```bash
# 1. Установите зависимости
pip install -r requirements.txt

# 2. Сгенерируйте конфигурацию
python generate_fabric_config.py

# 3. Сгенерируйте криптографические материалы и артефакты (требует Docker)
python generate_crypto_materials.py

# 4. Запустите сеть
python network_setup.py start

# 5. Создайте и настройте канал
python channel_setup.py
```

## Структура проекта

```
.
├── config/                        # Конфигурационные файлы (генерируется)
│   ├── crypto-config.yaml         # Конфигурация для генерации криптографических материалов
│   └── configtx.yaml              # Конфигурация для генерации транзакций канала
├── organizations/                 # Криптографические материалы организаций (генерируется)
│   ├── ordererOrganizations/
│   └── peerOrganizations/
├── channel-artifacts/             # Артефакты канала (генерируется)
│   ├── genesis.block
│   ├── npa-channel.tx
│   ├── Org1MSPanchors.tx
│   └── Org2MSPanchors.tx
├── docker-compose.yaml            # Docker Compose конфигурация (генерируется)
├── generate_fabric_config.py      # Скрипт генерации конфигурации
├── generate_crypto_materials.py   # Скрипт генерации криптографических материалов
├── channel_setup.py               # Скрипт для создания и настройки канала
├── network_setup.py               # Скрипт для управления сетью
├── requirements.txt               # Python зависимости
└── README.md                      # Документация
```

## Требования

- Python 3.7+
- Docker и Docker Compose
- Hyperledger Fabric инструменты (cryptogen, configtxgen) - опционально для ручной генерации

## Установка

1. Установите зависимости Python:
```bash
pip install -r requirements.txt
```

2. Сгенерируйте конфигурацию:
```bash
python generate_fabric_config.py
```

## Генерация криптографических материалов и артефактов

Для генерации криптографических материалов и артефактов канала вам понадобятся инструменты Hyperledger Fabric.

### Вариант 1: Использование официальных инструментов Fabric

1. Скачайте и установите Hyperledger Fabric binaries:
```bash
# Пример для Linux
curl -sSL https://bit.ly/2ysbOFE | bash -s -- 2.5.0
```

2. Генерация криптографических материалов:
```bash
cryptogen generate --config=./config/crypto-config.yaml --output=./organizations
```

3. Генерация genesis блока:
```bash
export FABRIC_CFG_PATH=$PWD/config
configtxgen -profile TwoOrgsOrdererGenesis -channelID system-channel -outputBlock ./channel-artifacts/genesis.block
```

4. Генерация транзакции создания канала:
```bash
configtxgen -profile TwoOrgsChannel -channelID npa-channel -outputCreateChannelTx ./channel-artifacts/npa-channel.tx
```

5. Генерация anchor peer транзакций:
```bash
configtxgen -profile TwoOrgsChannel -outputAnchorPeersUpdate ./channel-artifacts/Org1MSPanchors.tx -channelID npa-channel -asOrg Org1MSP
configtxgen -profile TwoOrgsChannel -outputAnchorPeersUpdate ./channel-artifacts/Org2MSPanchors.tx -channelID npa-channel -asOrg Org2MSP
```

### Вариант 2: Использование Docker образов Fabric

Если у вас установлен Docker, вы можете использовать официальные образы Fabric:

```bash
# Генерация криптографических материалов
docker run --rm -v "$PWD":/data -w /data hyperledger/fabric-tools:2.5 cryptogen generate --config=./config/crypto-config.yaml --output=./organizations

# Генерация genesis блока
docker run --rm -v "$PWD":/data -w /data -e FABRIC_CFG_PATH=/data/config hyperledger/fabric-tools:2.5 configtxgen -profile TwoOrgsOrdererGenesis -channelID system-channel -outputBlock ./channel-artifacts/genesis.block

# Генерация транзакции создания канала
docker run --rm -v "$PWD":/data -w /data -e FABRIC_CFG_PATH=/data/config hyperledger/fabric-tools:2.5 configtxgen -profile TwoOrgsChannel -channelID npa-channel -outputCreateChannelTx ./channel-artifacts/npa-channel.tx

# Генерация anchor peer транзакций
docker run --rm -v "$PWD":/data -w /data -e FABRIC_CFG_PATH=/data/config hyperledger/fabric-tools:2.5 configtxgen -profile TwoOrgsChannel -outputAnchorPeersUpdate ./channel-artifacts/Org1MSPanchors.tx -channelID npa-channel -asOrg Org1MSP
docker run --rm -v "$PWD":/data -w /data -e FABRIC_CFG_PATH=/data/config hyperledger/fabric-tools:2.5 configtxgen -profile TwoOrgsChannel -outputAnchorPeersUpdate ./channel-artifacts/Org2MSPanchors.tx -channelID npa-channel -asOrg Org2MSP
```

## Запуск сети

После генерации всех необходимых артефактов:

```bash
docker-compose up -d
```

Проверка статуса контейнеров:
```bash
docker-compose ps
```

Просмотр логов:
```bash
docker-compose logs -f
```

## Остановка сети

```bash
docker-compose down
```

Для полной очистки (включая volumes):
```bash
docker-compose down -v
```

## Компоненты сети

- **Fabric CA Orderer**: ca_orderer (порт 7054)
- **Fabric CA Org1**: ca_org1 (порт 7054)
- **Fabric CA Org2**: ca_org2 (порт 8054)
- **Orderer**: orderer0 (порт 7050)
- **Org1 Peer**: peer0.org1.example.com (порт 7051)
- **Org2 Peer**: peer0.org2.example.com (порт 9051)
- **CouchDB для Org1**: couchdb0 (порт 5984)
- **CouchDB для Org2**: couchdb1 (порт 5985)

## Создание и настройка канала

После запуска сети, для создания и настройки канала `npa-channel` используйте автоматизированный скрипт:

```bash
# Полная настройка канала (создание + join + anchor update)
python channel_setup.py

# Или с указанием имени канала
python channel_setup.py --channel npa-channel
```

### Отдельные операции

```bash
# Только создать канал
python channel_setup.py --create-only

# Только присоединить peer'ы к каналу
python channel_setup.py --join-only

# Только обновить anchor peer'ы
python channel_setup.py --anchor-only

# Выполнить операцию для конкретной организации
python channel_setup.py --join-only --org Org1
python channel_setup.py --anchor-only --org Org2
```

### Ручное создание канала (альтернатива)

Если вы предпочитаете выполнять команды вручную:

```bash
# От имени Org1
export CORE_PEER_LOCALMSPID=Org1MSP
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_MSPCONFIGPATH=./organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051
export CORE_PEER_TLS_ROOTCERT_FILE=./organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export ORDERER_CA=./organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem

# Создание канала
peer channel create -o localhost:7050 -c npa-channel --ordererTLSHostnameOverride orderer.example.com -f ./channel-artifacts/npa-channel.tx --outputBlock ./channel-artifacts/npa-channel.block --tls --cafile $ORDERER_CA

# Присоединение Org1 к каналу
peer channel join -b ./channel-artifacts/npa-channel.block

# Обновление anchor peer для Org1
peer channel update -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com -c npa-channel -f ./channel-artifacts/Org1MSPanchors.tx --tls --cafile $ORDERER_CA

# Присоединение Org2 к каналу
export CORE_PEER_LOCALMSPID=Org2MSP
export CORE_PEER_MSPCONFIGPATH=./organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=localhost:9051
export CORE_PEER_TLS_ROOTCERT_FILE=./organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt

peer channel join -b ./channel-artifacts/npa-channel.block

# Обновление anchor peer для Org2
peer channel update -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com -c npa-channel -f ./channel-artifacts/Org2MSPanchors.tx --tls --cafile $ORDERER_CA
```

## Примечания

- Все конфигурационные файлы генерируются на Python
- Структура соответствует стандартам Hyperledger Fabric v2.x
- Используется etcdraft как консенсусный алгоритм
- CouchDB используется как state database для обоих peer'ов

