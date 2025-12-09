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

**⚠️ Важно:** Этот скрипт автоматически:
- Останавливает запущенную сеть (если есть)
- Удаляет старые криптографические материалы и артефакты
- Генерирует новые материалы

Это необходимо для избежания конфликтов сертификатов. Если вы хотите сохранить старые материалы, используйте флаг `--no-cleanup` (не рекомендуется).

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

**⚠️ Важно:** Если после создания канала высота канала равна 1 и появляются ошибки "no endpoints currently defined", это означает, что канал был создан со старой конфигурацией. В этом случае:

1. Остановите сеть и очистите volumes:
   ```bash
   python network_setup.py clean
   docker volume rm orderer0  # Убедитесь, что volume orderer удален
   ```

2. Перегенерируйте материалы:
   ```bash
   python generate_crypto_materials.py
   ```

3. Запустите сеть и пересоздайте канал:
   ```bash
   python network_setup.py start
   python channel_setup.py
   ```

4. Проверьте высоту канала (должна быть больше 1):
   ```bash
   docker exec peer0.org1.example.com peer channel getinfo -c npa-channel
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

## Полный справочник команд

### Генерация конфигурации

#### `generate_fabric_config.py` - Генерация базовой конфигурации сети

**Команда:**
```bash
python generate_fabric_config.py
```

**Результат:**
- Создает директорию `config/`
- Генерирует `config/crypto-config.yaml` - конфигурация для криптографических материалов
- Генерирует `config/configtx.yaml` - конфигурация для транзакций канала
- Генерирует `docker-compose.yaml` - конфигурация Docker Compose для всей сети
- Создает структуру директорий для организаций

**Когда использовать:** В начале настройки проекта, один раз или после изменения структуры сети.

---

### Генерация криптографических материалов

#### `generate_crypto_materials.py` - Генерация сертификатов и артефактов

**Команда:**
```bash
python generate_crypto_materials.py [--channel CHANNEL_NAME] [--platform PLATFORM] [--no-cleanup]
```

**Аргументы:**
- `--channel` - Имя канала (по умолчанию: `npa-channel`)
- `--platform` - Платформа Docker образа: `linux/amd64` или `linux/arm64` (определяется автоматически, если не указано)
- `--no-cleanup` - Не очищать старые материалы перед генерацией (не рекомендуется)

**Результат:**
- Останавливает запущенную сеть (если есть)
- Удаляет старые криптографические материалы (`organizations/`) и артефакты (`channel-artifacts/`)
- Генерирует новые сертификаты и ключи для всех компонентов сети
- Создает `channel-artifacts/genesis.block` - genesis блок для orderer
- Создает `channel-artifacts/npa-channel.tx` - транзакция создания канала
- Создает `channel-artifacts/Org1MSPanchors.tx` - транзакция anchor peer для Org1
- Создает `channel-artifacts/Org2MSPanchors.tx` - транзакция anchor peer для Org2

**Примеры:**
```bash
# Стандартная генерация
python generate_crypto_materials.py

# Генерация для другого канала
python generate_crypto_materials.py --channel my-channel

# Генерация без очистки (не рекомендуется)
python generate_crypto_materials.py --no-cleanup
```

**Когда использовать:** После генерации конфигурации, после изменения организаций, при необходимости пересоздать материалы.

---

### Управление сетью

#### `network_setup.py start` - Запуск сети

**Команда:**
```bash
python network_setup.py start
```

**Результат:**
- Проверяет наличие Docker и Docker Compose
- Проверяет наличие конфигурационных файлов
- Запускает все контейнеры сети в фоновом режиме:
  - `ca_orderer`, `ca_org1`, `ca_org2` - Fabric CA серверы
  - `orderer0` - Orderer node
  - `peer0.org1.example.com`, `peer0.org2.example.com` - Peer nodes
  - `couchdb0`, `couchdb1` - CouchDB для state database

**Альтернатива:**
```bash
docker compose up -d
```

**Когда использовать:** После генерации материалов и перед созданием канала.

---

#### `network_setup.py stop` - Остановка сети

**Команда:**
```bash
python network_setup.py stop
```

**Результат:**
- Останавливает все контейнеры сети
- **НЕ удаляет** Docker volumes (данные сохраняются)
- Контейнеры можно перезапустить без потери данных

**Альтернатива:**
```bash
docker compose down
```

**Когда использовать:** Для временной остановки сети без потери данных.

---

#### `network_setup.py clean` - Остановка с очисткой volumes

**Команда:**
```bash
python network_setup.py clean
```

**Результат:**
- Останавливает все контейнеры сети
- **Удаляет** все Docker volumes (все данные удаляются)
- При следующем запуске сеть начнется "с чистого листа"

**Альтернатива:**
```bash
docker compose down -v
```

**Когда использовать:** При необходимости полностью очистить сеть (например, при пересоздании канала или после ошибок).

---

#### `network_setup.py status` - Статус сети

**Команда:**
```bash
python network_setup.py status
```

**Результат:**
- Показывает статус всех контейнеров сети
- Отображает состояние (Running, Exited, etc.)
- Показывает порты и время работы

**Альтернатива:**
```bash
docker compose ps -a
```

**Когда использовать:** Для проверки состояния сети перед выполнением операций.

---

#### `network_setup.py logs` - Просмотр логов

**Команда:**
```bash
python network_setup.py logs
```

**Результат:**
- Показывает логи всех контейнеров в реальном времени
- Последние 100 строк логов каждого контейнера
- Логи обновляются в реальном времени (режим `follow`)

**Альтернатива:**
```bash
docker compose logs -f --tail=100
```

**Остановка:** Нажмите `Ctrl+C` для выхода

**Когда использовать:** Для отладки проблем сети, проверки работы компонентов.

---

### Настройка канала

#### `channel_setup.py` - Полная настройка канала (по умолчанию)

**Команда:**
```bash
python channel_setup.py [--channel CHANNEL_NAME] [--force-recreate]
```

**Аргументы:**
- `--channel` - Имя канала (по умолчанию: `npa-channel`)
- `--force-recreate` - Принудительно пересоздать канал (удалив старый локальный блок)

**Результат:**
- Проверяет наличие необходимых файлов (`.tx` транзакции)
- Проверяет запущенные контейнеры
- Ожидает готовности orderer (до 30 секунд)
- Создает канал
- Присоединяет все peer'ы к каналу
- Обновляет anchor peer для всех организаций

**Примеры:**
```bash
# Стандартная настройка канала npa-channel
python channel_setup.py

# Настройка другого канала
python channel_setup.py --channel my-channel

# Пересоздание канала
python channel_setup.py --force-recreate
```

**Когда использовать:** После запуска сети для первоначальной настройки канала или после изменений конфигурации.

---

#### `channel_setup.py --create-only` - Только создание канала

**Команда:**
```bash
python channel_setup.py --create-only [--channel CHANNEL_NAME] [--force-recreate]
```

**Результат:**
- Создает только транзакцию создания канала
- **Не присоединяет** peer'ы и **не обновляет** anchor peer

**Когда использовать:** При ручной настройке канала пошагово.

---

#### `channel_setup.py --join-only` - Только присоединение peer'ов

**Команда:**
```bash
python channel_setup.py --join-only [--channel CHANNEL_NAME] [--org Org1|Org2]
```

**Результат:**
- Присоединяет peer'ы к существующему каналу
- Если указан `--org`, присоединяет только указанную организацию
- Если `--org` не указан, присоединяет все организации

**Примеры:**
```bash
# Присоединить все организации
python channel_setup.py --join-only

# Присоединить только Org1
python channel_setup.py --join-only --org Org1
```

**Когда использовать:** Для присоединения нового peer'а к существующему каналу.

---

#### `channel_setup.py --anchor-only` - Только обновление anchor peer

**Команда:**
```bash
python channel_setup.py --anchor-only [--channel CHANNEL_NAME] [--org Org1|Org2]
```

**Результат:**
- Обновляет только anchor peer для организаций
- Если указан `--org`, обновляет только указанную организацию
- Если `--org` не указан, обновляет все организации

**Примеры:**
```bash
# Обновить anchor peer для всех организаций
python channel_setup.py --anchor-only

# Обновить anchor peer только для Org2
python channel_setup.py --anchor-only --org Org2
```

**Когда использовать:** При необходимости обновить anchor peer после изменений конфигурации.

---

### Развертывание chaincode

#### `deploy_chaincode.py` - Полное развертывание chaincode

**Команда:**
```bash
cd chaincode
python deploy_chaincode.py [--channel CHANNEL_NAME] [--name CHAINCODE_NAME] [--version VERSION] [--sequence SEQUENCE]
```

**Аргументы:**
- `--channel` - Имя канала (по умолчанию: `npa-channel`)
- `--name` - Имя chaincode (по умолчанию: `taskdocument`)
- `--version` - Версия chaincode (по умолчанию: `1.0`)
- `--sequence` - Sequence номер (по умолчанию: `1`)

**Результат:**
- Создает package для external chaincode (CCAAS)
- Устанавливает chaincode на peer'ы обеих организаций
- Одобряет chaincode от имени обеих организаций
- Проверяет готовность к коммиту
- Коммитит chaincode в канал

**Примеры:**
```bash
# Стандартное развертывание
python deploy_chaincode.py

# Развертывание с другой версией
python deploy_chaincode.py --version 2.0 --sequence 2

# Развертывание в другой канал
python deploy_chaincode.py --channel my-channel
```

**Когда использовать:** После настройки канала для развертывания chaincode приложения.

---

### Полезные Docker команды

#### Просмотр логов конкретного контейнера

```bash
# Логи orderer
docker logs orderer0 --tail 100 -f

# Логи peer Org1
docker logs peer0.org1.example.com --tail 100 -f

# Логи peer Org2
docker logs peer0.org2.example.com --tail 100 -f
```

#### Проверка высоты канала

```bash
# Проверка высоты канала на peer Org1
docker exec peer0.org1.example.com peer channel getinfo -c npa-channel

# Проверка высоты канала на peer Org2
docker exec peer0.org2.example.com peer channel getinfo -c npa-channel
```

#### Просмотр списка каналов на peer

```bash
# Список каналов на peer Org1
docker exec -e CORE_PEER_LOCALMSPID=Org1MSP -e CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/admin-msp peer0.org1.example.com peer channel list

# Список каналов на peer Org2
docker exec -e CORE_PEER_LOCALMSPID=Org2MSP -e CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/admin-msp peer0.org2.example.com peer channel list
```

#### Удаление конкретного volume

```bash
# Удаление volume orderer (для пересоздания канала)
docker volume rm nir_orderer0

# Или найти правильное имя volume
docker volume ls | Select-String orderer

# Удаление volume peer
docker volume rm nir_peer0.org1.example.com
docker volume rm nir_peer0.org2.example.com
```

#### Проверка сетевых подключений

```bash
# Проверка Docker сети
docker network ls
docker network inspect nir_fabric-network

# Проверка подключения к orderer из peer
docker exec peer0.org1.example.com ping -c 3 orderer0
```

---

### Типичные последовательности команд

#### Первоначальная настройка сети

```bash
# 1. Генерация конфигурации
python generate_fabric_config.py

# 2. Генерация криптографических материалов
python generate_crypto_materials.py

# 3. Запуск сети
python network_setup.py start

# 4. Ожидание запуска (рекомендуется 20-30 секунд)
Start-Sleep -Seconds 25

# 5. Создание и настройка канала
python channel_setup.py

# 6. Проверка высоты канала (должна быть > 1)
docker exec peer0.org1.example.com peer channel getinfo -c npa-channel

# 7. Развертывание chaincode
cd chaincode
python deploy_chaincode.py
```

#### Пересоздание канала

```bash
# 1. Остановка сети с очисткой
python network_setup.py clean

# 2. Перегенерирование материалов
python generate_crypto_materials.py

# 3. Запуск сети
python network_setup.py start

# 4. Ожидание запуска
Start-Sleep -Seconds 25

# 5. Пересоздание канала
python channel_setup.py --force-recreate
```

#### Обновление chaincode

```bash
cd chaincode

# Развертывание новой версии (увеличьте sequence)
python deploy_chaincode.py --version 2.0 --sequence 2
```

#### Отладка проблем

```bash
# 1. Проверка статуса сети
python network_setup.py status

# 2. Просмотр логов
python network_setup.py logs

# 3. Проверка конкретного контейнера
docker logs orderer0 --tail 100

# 4. Проверка высоты канала
docker exec peer0.org1.example.com peer channel getinfo -c npa-channel
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
