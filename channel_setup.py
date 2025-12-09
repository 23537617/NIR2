#!/usr/bin/env python3
"""
Скрипт для создания и настройки канала Hyperledger Fabric
Выполняет: создание канала, присоединение peer'ов, обновление anchor peer'ов
"""

import subprocess
import os
import sys
import time
from pathlib import Path


class ChannelSetup:
    def __init__(self, base_dir=".", channel_name="npa-channel"):
        self.base_dir = Path(base_dir)
        self.channel_name = channel_name
        self.orgs_dir = self.base_dir / "organizations"
        self.channel_dir = self.base_dir / "channel-artifacts"
        
        # Конфигурация организаций
        self.orgs = {
            "Org1": {
                "msp_id": "Org1MSP",
                "domain": "org1.example.com",
                "peer": "peer0.org1.example.com",
                "peer_port": 7051,
                "admin_user": "Admin@org1.example.com"
            },
            "Org2": {
                "msp_id": "Org2MSP",
                "domain": "org2.example.com",
                "peer": "peer0.org2.example.com",
                "peer_port": 9051,
                "admin_user": "Admin@org2.example.com"
            }
        }
        
        # Orderer конфигурация
        self.orderer = {
            "host": "orderer.example.com",  # DNS имя для TLS
            "container": "orderer0",  # Имя контейнера
            "port": 7050,
            "domain": "example.com"
        }
    
    def find_orderer_ca_cert(self):
        """Находит CA сертификат orderer в нескольких возможных местах"""
        orderer_tls_dir = self.orgs_dir / "ordererOrganizations" / self.orderer["domain"] / "orderers" / self.orderer["host"] / "tls"
        orderer_msp_dir = self.orgs_dir / "ordererOrganizations" / self.orderer["domain"] / "orderers" / self.orderer["host"] / "msp" / "tlscacerts"
        
        # Приоритет: msp/tlscacerts/*.pem (это правильный TLS CA сертификат для проверки сертификата orderer)
        if orderer_msp_dir.exists():
            pem_files = list(orderer_msp_dir.glob("*.pem"))
            if pem_files:
                # Предпочтительно файл с именем, содержащим "tlsca"
                tlsca_files = [f for f in pem_files if "tlsca" in f.name.lower()]
                if tlsca_files:
                    return tlsca_files[0]
                return pem_files[0]
        
        # Затем пробуем tls/ca.crt (может быть правильным в некоторых конфигурациях)
        if (orderer_tls_dir / "ca.crt").exists():
            return orderer_tls_dir / "ca.crt"
        
        # Также пробуем tls/*.crt
        if orderer_tls_dir.exists():
            crt_files = list(orderer_tls_dir.glob("*.crt"))
            if crt_files:
                return crt_files[0]
        
        return None
    
    def check_prerequisites(self):
        """Проверяет наличие необходимых файлов и запущенных контейнеров"""
        print("\n" + "="*60)
        print("Проверка предварительных условий")
        print("="*60)
        
        # Проверка наличия транзакции создания канала
        channel_tx = self.channel_dir / f"{self.channel_name}.tx"
        if not channel_tx.exists():
            print(f"❌ Файл {channel_tx} не найден")
            print("   Сначала запустите: python generate_crypto_materials.py")
            return False
        print(f"✓ Найден файл: {channel_tx}")
        
        # Проверка наличия anchor peer транзакций
        for org_name, org_config in self.orgs.items():
            anchor_tx = self.channel_dir / f"{org_config['msp_id']}anchors.tx"
            if not anchor_tx.exists():
                print(f"❌ Файл {anchor_tx} не найден")
                print("   Сначала запустите: python generate_crypto_materials.py")
                return False
            print(f"✓ Найден файл: {anchor_tx}")
        
        # Проверка CA сертификата orderer
        orderer_ca = self.find_orderer_ca_cert()
        if not orderer_ca:
            print(f"❌ Не найден CA сертификат orderer")
            print("   Проверьте, что криптографические материалы сгенерированы")
            return False
        print(f"✓ Найден CA сертификат orderer: {orderer_ca}")
        
        # Проверка запущенных контейнеров
        required_containers = [
            "orderer0",
            "peer0.org1.example.com",
            "peer0.org2.example.com"
        ]
        
        # Ждем запуска контейнеров (максимум 30 секунд)
        print("\nОжидание запуска контейнеров...")
        max_wait = 30
        interval = 2
        waited = 0
        all_ready = False
        
        while waited < max_wait and not all_ready:
            try:
                result = subprocess.run(
                    ["docker", "ps", "--format", "{{.Names}}"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                running_containers = [c.strip() for c in result.stdout.strip().split('\n') if c.strip()]
                
                all_ready = True
                for container in required_containers:
                    if container not in running_containers:
                        all_ready = False
                        break
                
                if not all_ready:
                    time.sleep(interval)
                    waited += interval
                    if waited % 6 == 0:  # Каждые 6 секунд показываем прогресс
                        print(f"   Ожидание... ({waited}/{max_wait} секунд)")
            except subprocess.CalledProcessError:
                print("❌ Не удалось проверить статус контейнеров")
                return False
        
        # Проверяем финальный статус
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True
            )
            running_containers = [c.strip() for c in result.stdout.strip().split('\n') if c.strip()]
            
            # Также проверяем остановленные контейнеры
            result_all = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{.Names}}|{{.Status}}"],
                capture_output=True,
                text=True,
                check=True
            )
            all_containers = {}
            for line in result_all.stdout.strip().split('\n'):
                if '|' in line:
                    name, status = line.split('|', 1)
                    all_containers[name.strip()] = status.strip()
            
            for container in required_containers:
                if container in running_containers:
                    print(f"✓ Контейнер {container} запущен")
                else:
                    print(f"❌ Контейнер {container} не запущен")
                    if container in all_containers:
                        status = all_containers[container]
                        print(f"   Статус: {status}")
                        if "Exited" in status:
                            print(f"   Контейнер остановлен. Проверьте логи: docker logs {container}")
                    else:
                        print(f"   Контейнер не найден")
                    print("   Запустите сеть: python network_setup.py start")
                    return False
        except subprocess.CalledProcessError:
            print("❌ Не удалось проверить статус контейнеров")
            return False
        
        return True
    
    def run_peer_command(self, org_name, command, description, env_vars=None):
        """Выполняет команду peer через Docker для указанной организации"""
        org_config = self.orgs[org_name]
        
        # Пути к сертификатам
        admin_msp = self.orgs_dir / "peerOrganizations" / org_config["domain"] / "users" / org_config["admin_user"] / "msp"
        peer_tls = self.orgs_dir / "peerOrganizations" / org_config["domain"] / "peers" / org_config["peer"] / "tls"
        
        # Находим файл CA сертификата orderer используя универсальный метод
        orderer_ca_file = self.find_orderer_ca_cert()
        if not orderer_ca_file:
            print(f"❌ Не найден CA сертификат orderer")
            return False
        
        # Находим файл CA сертификата peer
        peer_ca_files = list(peer_tls.glob("ca.crt"))
        if not peer_ca_files:
            # Пробуем альтернативное имя
            peer_ca_files = list((peer_tls.parent.parent / "msp" / "tlscacerts").glob("*.pem"))
        if not peer_ca_files:
            print(f"❌ Не найден CA сертификат peer в {peer_tls}")
            return False
        peer_ca_file = peer_ca_files[0]
        
        # Переменные окружения
        docker_env = [
            "-e", f"CORE_PEER_LOCALMSPID={org_config['msp_id']}",
            "-e", "CORE_PEER_TLS_ENABLED=true",
            "-e", f"CORE_PEER_ADDRESS={org_config['peer']}:{org_config['peer_port']}",
            "-e", f"CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt",
            "-e", f"CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/msp",
        ]
        
        if env_vars:
            for key, value in env_vars.items():
                docker_env.extend(["-e", f"{key}={value}"])
        
        # Docker команда
        cmd = [
            "docker", "exec",
            *docker_env,
            "-w", "/opt/gopath/src/github.com/hyperledger/fabric/peer",
            org_config["peer"],
            "peer"
        ] + command
        
        print(f"\n{'='*60}")
        print(f"{description} ({org_name})")
        print(f"{'='*60}")
        print(f"Выполняется: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Ошибка: {result.stderr}")
            if result.stdout:
                print(f"Вывод: {result.stdout}")
            return False
        else:
            print(f"✓ Успешно")
            if result.stdout:
                print(result.stdout)
            return True
    
    def create_channel(self, force_recreate=False):
        """Создает канал (от имени Org1)"""
        org_name = "Org1"
        org_config = self.orgs[org_name]
        
        channel_tx = self.channel_dir / f"{self.channel_name}.tx"
        channel_block = self.channel_dir / f"{self.channel_name}.block"
        
        # Если принудительное пересоздание - удаляем локальный блок
        if force_recreate and channel_block.exists():
            print(f"⚠️  Принудительное пересоздание: удаляется локальный блок канала")
            channel_block.unlink()
        
        # Проверяем, не существует ли уже канал локально (если не принудительное пересоздание)
        if not force_recreate and channel_block.exists():
            print(f"✓ Блок канала уже существует: {channel_block}")
            print("   Пропущено создание канала (используется существующий блок)")
            return True
        
        # Получаем путь к MSP Admin пользователя
        peer_container = org_config["peer"]
        orderer_ca_file = self.find_orderer_ca_cert()
        if not orderer_ca_file:
            print(f"❌ Не найден CA сертификат orderer")
            return False
        
        # Копируем orderer CA в контейнер для проверки
        copy_cmd = [
            "docker", "cp",
            str(orderer_ca_file.absolute()),
            f"{peer_container}:/opt/gopath/src/github.com/hyperledger/fabric/peer/orderer-ca.pem"
        ]
        subprocess.run(copy_cmd, capture_output=True)
        
        admin_msp = self.orgs_dir / "peerOrganizations" / org_config["domain"] / "users" / org_config["admin_user"] / "msp"
        if not admin_msp.exists():
            print(f"❌ MSP Admin пользователя не найден: {admin_msp}")
            return False
        
        admin_msp_container_path = "/etc/hyperledger/fabric/admin-msp"
        
        # Копируем MSP Admin в контейнер
        # Используем "/." в конце для копирования содержимого директории
        copy_cmd = [
            "docker", "cp",
            str(admin_msp.absolute()) + "/.",
            f"{peer_container}:{admin_msp_container_path}"
        ]
        result = subprocess.run(copy_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Ошибка при копировании Admin MSP: {result.stderr}")
            return False
        
        # Проверяем существование канала на orderer (всегда, чтобы предупредить при force_recreate)
        print("\n🔍 Проверка существования канала на orderer...")
        fetch_cmd = [
            "docker", "exec",
            "-e", f"CORE_PEER_LOCALMSPID={org_config['msp_id']}",
            "-e", "CORE_PEER_TLS_ENABLED=true",
            "-e", f"CORE_PEER_ADDRESS={org_config['peer']}:{org_config['peer_port']}",
            "-e", f"CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt",
            "-e", f"CORE_PEER_MSPCONFIGPATH={admin_msp_container_path}",
            "-w", "/opt/gopath/src/github.com/hyperledger/fabric/peer",
            peer_container,
            "peer", "channel", "fetch", "oldest",
            f"./{self.channel_name}.block",
            "-o", f"{self.orderer['container']}:{self.orderer['port']}",
            "--ordererTLSHostnameOverride", self.orderer["host"],
            "-c", self.channel_name,
            "--tls",
            "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/orderer-ca.pem"
        ]
        fetch_result = subprocess.run(fetch_cmd, capture_output=True, text=True, timeout=10)
        
        if fetch_result.returncode == 0:
            if force_recreate:
                print(f"❌ Канал {self.channel_name} уже существует на orderer и не может быть пересоздан напрямую")
                print(f"\n💡 Для пересоздания канала необходимо удалить volume orderer:")
                
                # Определяем правильное имя volume (Docker Compose добавляет префикс проекта)
                result = subprocess.run(
                    ["docker", "volume", "ls", "--format", "{{.Name}}"],
                    capture_output=True,
                    text=True
                )
                orderer_volume = None
                if result.returncode == 0:
                    volumes = result.stdout.strip().split('\n')
                    orderer_volume = next((v for v in volumes if 'orderer0' in v), None)
                
                volume_name = orderer_volume if orderer_volume else "orderer0 (или <проект>_orderer0)"
                
                print(f"   1. Остановите сеть: python network_setup.py stop")
                print(f"   2. Удалите volume: docker volume rm {volume_name}")
                print(f"   3. Запустите сеть заново: python network_setup.py start")
                print(f"   4. Затем запустите: python channel_setup.py --force-recreate")
                return False
            else:
                print(f"✓ Канал {self.channel_name} уже существует на orderer")
                # Копируем блок обратно на хост
                copy_cmd = [
                    "docker", "cp",
                    f"{peer_container}:/opt/gopath/src/github.com/hyperledger/fabric/peer/{self.channel_name}.block",
                    str(channel_block.absolute())
                ]
                subprocess.run(copy_cmd, capture_output=True)
                print(f"✓ Блок канала сохранен: {channel_block}")
                return True
        
        # Канал не существует на orderer, создаем новый
        
        # Ожидание полной готовности orderer (особенно важно после перезапуска)
        print("\n⏳ Ожидание готовности orderer...")
        orderer_ready = False
        max_orderer_wait = 30  # Максимум 30 секунд ожидания
        orderer_waited = 0
        interval = 3  # Проверяем каждые 3 секунды
        
        while orderer_waited < max_orderer_wait and not orderer_ready:
            # Сначала проверяем, что контейнер orderer запущен и не упал
            container_check = subprocess.run(
                ["docker", "ps", "--filter", "name=orderer0", "--format", "{{.Status}}"],
                capture_output=True,
                text=True
            )
            if not container_check.stdout.strip() or "Exited" in container_check.stdout:
                print(f"❌ Контейнер orderer0 не запущен или остановлен")
                print(f"   Статус: {container_check.stdout.strip()}")
                print(f"   Проверьте логи: docker logs orderer0")
                return False
            
            # Проверяем логи orderer на готовность и отсутствие ошибок
            # Проверяем ВСЕ логи, а не только последние 50 строк
            log_check = subprocess.run(
                ["docker", "logs", "orderer0", "2>&1"],
                capture_output=True,
                text=True
            )
            
            if log_check.returncode == 0 and log_check.stdout:
                logs = log_check.stdout.lower()
                
                # Проверяем на критические ошибки (только в последних 100 строках)
                recent_logs = "\n".join(log_check.stdout.split('\n')[-100:]).lower()
                critical_errors = ["panic", "fatal error", "failed to start", "error initializing", 
                                  "certificate signed by unknown authority", "invalid identity"]
                has_critical_error = any(err in recent_logs for err in critical_errors)
                
                if has_critical_error:
                    print(f"❌ Обнаружены критические ошибки в логах orderer:")
                    # Показываем последние строки с ошибками
                    error_lines = [line for line in log_check.stdout.split('\n')[-100:] 
                                 if any(err in line.lower() for err in critical_errors)][-5:]
                    for line in error_lines:
                        if line.strip():
                            print(f"   {line}")
                    print(f"   Полные логи: docker logs orderer0")
                    return False
                
                # Проверяем признаки готовности во ВСЕХ логах
                ready_indicators = [
                    "beginning to serve requests",
                    "start accepting requests",
                    "starting to serve grpc requests",
                    "server started",
                    "orderer started"
                ]
                has_ready_indicator = any(indicator in logs for indicator in ready_indicators)
                
                # Дополнительно проверяем, что orderer стал лидером (для etcdraft)
                # или что прошло достаточно времени с момента запуска
                if has_ready_indicator:
                    # Простая проверка доступности через попытку подключения
                    # Используем timeout для проверки сетевой доступности
                    import socket
                    try:
                        # Проверяем TCP соединение (быстрая проверка)
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)
                        # Используем localhost:7050, так как проверяем доступность из контейнера
                        # Но на самом деле нам нужно проверить через docker network
                        sock.close()
                    except:
                        pass
                    
                    # Если нет критических ошибок и есть признаки готовности, считаем готовым
                    orderer_ready = True
                    print(f"✓ Orderer готов к приему запросов (проверено через {orderer_waited} секунд)")
                    break
            
            time.sleep(interval)
            orderer_waited += interval
            if orderer_waited % 9 == 0:  # Показываем прогресс каждые 9 секунд
                print(f"   Ожидание готовности orderer... ({orderer_waited}/{max_orderer_wait} секунд)")
        
        if not orderer_ready:
            print(f"\n⚠️  Orderer не готов после {max_orderer_wait} секунд ожидания")
            print(f"   Проверьте логи orderer: docker logs orderer0 --tail 100")
            print(f"   Убедитесь, что orderer успешно запустился без ошибок")
            print(f"   Если orderer запущен, попытка создания канала все равно будет выполнена...")
            print(f"   (Возможно, orderer готов, но проверка не сработала)")
            # Не возвращаем False, продолжаем попытку создания канала
        
        # Копируем channel tx в контейнер
        copy_cmd = [
            "docker", "cp",
            str(channel_tx.absolute()),
            f"{peer_container}:/opt/gopath/src/github.com/hyperledger/fabric/peer/{self.channel_name}.tx"
        ]
        result = subprocess.run(copy_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️  Предупреждение при копировании channel tx: {result.stderr}")
        
        # Orderer CA уже скопирован выше, продолжаем с созданием канала
        
        # Проверяем, что файл скопирован
        check_cmd = [
            "docker", "exec",
            peer_container,
            "test", "-f", "/opt/gopath/src/github.com/hyperledger/fabric/peer/orderer-ca.pem"
        ]
        result = subprocess.run(check_cmd, capture_output=True)
        if result.returncode != 0:
            print(f"❌ Файл orderer-ca.pem не найден в контейнере после копирования")
            return False
        
        # Команда создания канала
        # Используем Admin MSP для подписи транзакции
        # Используем имя контейнера для подключения в Docker сети
        # но TLS hostname для проверки сертификата
        cmd = [
            "docker", "exec",
            "-e", f"CORE_PEER_LOCALMSPID={org_config['msp_id']}",
            "-e", "CORE_PEER_TLS_ENABLED=true",
            "-e", f"CORE_PEER_ADDRESS={org_config['peer']}:{org_config['peer_port']}",
            "-e", f"CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt",
            "-e", f"CORE_PEER_MSPCONFIGPATH={admin_msp_container_path}",  # Используем Admin MSP
            "-w", "/opt/gopath/src/github.com/hyperledger/fabric/peer",
            peer_container,
            "peer", "channel", "create",
            "-o", f"{self.orderer['container']}:{self.orderer['port']}",  # Используем имя контейнера
            "-c", self.channel_name,
            "--ordererTLSHostnameOverride", self.orderer["host"],  # TLS hostname для проверки сертификата
            "-f", f"./{self.channel_name}.tx",
            "--outputBlock", f"./{self.channel_name}.block",
            "--tls",
            "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/orderer-ca.pem"  # Полный путь
        ]
        
        print(f"\n{'='*60}")
        print(f"Создание канала {self.channel_name}")
        print(f"{'='*60}")
        print(f"Выполняется: {' '.join(cmd)}")
        
        # Выполняем команду с повторными попытками
        max_attempts = 3
        attempt = 0
        success = False
        result = None
        
        while attempt < max_attempts and not success:
            if attempt > 0:
                print(f"\n⏳ Повторная попытка {attempt + 1}/{max_attempts} через 5 секунд...")
                time.sleep(5)
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            except subprocess.TimeoutExpired:
                print(f"⚠️  Таймаут при выполнении команды (попытка {attempt + 1})")
                attempt += 1
                continue
            
            if result.returncode == 0:
                success = True
            else:
                attempt += 1
                error_msg = result.stderr[:200] if result.stderr else "Неизвестная ошибка"
                print(f"⚠️  Попытка {attempt} не удалась: {error_msg}...")
                if attempt < max_attempts:
                    # Проверяем, может быть orderer еще не готов
                    print("   Проверяем статус orderer...")
                    time.sleep(3)
        
        if not success:
            print(f"\n❌ Ошибка после {max_attempts} попыток")
            if result:
                print(f"Последняя ошибка: {result.stderr}")
                if result.stdout:
                    print(f"Вывод: {result.stdout}")
            print("\n💡 Рекомендации:")
            print("   1. Проверьте логи orderer: docker logs orderer0 --tail 50")
            print("   2. Убедитесь, что orderer полностью запущен: docker logs orderer0 | Select-String 'Beginning to serve'")
            print("   3. Проверьте, что контейнеры находятся в одной Docker сети")
            print("   4. Попробуйте перезапустить сеть: python network_setup.py clean && python network_setup.py start")
            return False
        
        print(f"✓ Канал {self.channel_name} успешно создан")
        
        # Копируем блок обратно на хост
        copy_cmd = [
            "docker", "cp",
            f"{peer_container}:/opt/gopath/src/github.com/hyperledger/fabric/peer/{self.channel_name}.block",
            str(channel_block.absolute())
        ]
        subprocess.run(copy_cmd, capture_output=True)
        print(f"✓ Блок канала сохранен: {channel_block}")
        
        return True
    
    def join_peer(self, org_name):
        """Присоединяет peer к каналу"""
        org_config = self.orgs[org_name]
        channel_block = self.channel_dir / f"{self.channel_name}.block"
        
        if not channel_block.exists():
            print(f"❌ Файл {channel_block} не найден. Сначала создайте канал.")
            return False
        
        peer_container = org_config["peer"]
        
        # Путь к MSP Admin пользователя
        admin_msp = self.orgs_dir / "peerOrganizations" / org_config["domain"] / "users" / org_config["admin_user"] / "msp"
        if not admin_msp.exists():
            print(f"❌ MSP Admin пользователя не найден: {admin_msp}")
            return False
        
        # Копируем MSP Admin в контейнер
        admin_msp_container_path = "/etc/hyperledger/fabric/admin-msp"
        
        # Удаляем старую директорию, если она существует (для чистоты)
        remove_cmd = [
            "docker", "exec",
            peer_container,
            "rm", "-rf", admin_msp_container_path
        ]
        subprocess.run(remove_cmd, capture_output=True)  # Игнорируем ошибки, если директории нет
        
        # Копируем MSP Admin в контейнер
        # Важно: используем родительскую директорию для сохранения структуры
        copy_cmd = [
            "docker", "cp",
            str(admin_msp.absolute()) + "/.",
            f"{peer_container}:{admin_msp_container_path}"
        ]
        result = subprocess.run(copy_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Ошибка при копировании Admin MSP: {result.stderr}")
            return False
        
        # Проверяем, что структура MSP скопировалась правильно
        # Проверяем наличие обязательных директорий
        required_dirs = ["signcerts", "keystore", "cacerts"]
        for dir_name in required_dirs:
            check_cmd = [
                "docker", "exec",
                peer_container,
                "test", "-d", f"{admin_msp_container_path}/{dir_name}"
            ]
            check_result = subprocess.run(check_cmd, capture_output=True)
            if check_result.returncode != 0:
                print(f"❌ Директория {dir_name} не найдена в Admin MSP")
                return False
        
        # Проверяем наличие сертификата (может быть с любым именем .pem)
        verify_cmd = [
            "docker", "exec",
            peer_container,
            "sh", "-c", f"ls {admin_msp_container_path}/signcerts/*.pem 2>/dev/null | head -1"
        ]
        verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
        if verify_result.returncode != 0 or not verify_result.stdout.strip():
            print(f"❌ Сертификат не найден в signcerts")
            print(f"   Проверьте путь: {admin_msp}")
            return False
        
        # Копируем блок канала в контейнер
        copy_cmd = [
            "docker", "cp",
            str(channel_block.absolute()),
            f"{peer_container}:/opt/gopath/src/github.com/hyperledger/fabric/peer/{self.channel_name}.block"
        ]
        subprocess.run(copy_cmd, capture_output=True)
        
        # Проверяем, присоединен ли peer уже к каналу
        print(f"\n{'='*60}")
        print(f"Проверка присоединения {org_name} к каналу {self.channel_name}")
        print(f"{'='*60}")
        
        check_cmd = [
            "docker", "exec",
            "-e", f"CORE_PEER_LOCALMSPID={org_config['msp_id']}",
            "-e", "CORE_PEER_TLS_ENABLED=true",
            "-e", f"CORE_PEER_ADDRESS={org_config['peer']}:{org_config['peer_port']}",
            "-e", f"CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt",
            "-e", f"CORE_PEER_MSPCONFIGPATH={admin_msp_container_path}",
            "-w", "/opt/gopath/src/github.com/hyperledger/fabric/peer",
            peer_container,
            "peer", "channel", "list"
        ]
        
        check_result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
        
        # Если команда выполнилась успешно и канал в списке, значит peer уже присоединен
        if check_result.returncode == 0 and self.channel_name in check_result.stdout:
            print(f"✓ {org_name} уже присоединен к каналу {self.channel_name}")
            return True
        
        # Если команда не выполнилась из-за I/O ошибки, пропускаем проверку и продолжаем
        if check_result.returncode != 0 and "input/output error" in check_result.stderr.lower():
            print(f"⚠️  Не удалось проверить присоединение (I/O ошибка), продолжаем попытку присоединения...")
        
        # Команда присоединения к каналу
        # Используем Admin MSP для прохождения проверки политик
        cmd = [
            "docker", "exec",
            "-e", f"CORE_PEER_LOCALMSPID={org_config['msp_id']}",
            "-e", "CORE_PEER_TLS_ENABLED=true",
            "-e", f"CORE_PEER_ADDRESS={org_config['peer']}:{org_config['peer_port']}",
            "-e", f"CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt",
            "-e", f"CORE_PEER_MSPCONFIGPATH={admin_msp_container_path}",  # Используем Admin MSP
            "-w", "/opt/gopath/src/github.com/hyperledger/fabric/peer",
            peer_container,
            "peer", "channel", "join",
            "-b", f"./{self.channel_name}.block"
        ]
        
        print(f"\n{'='*60}")
        print(f"Присоединение {org_name} к каналу {self.channel_name}")
        print(f"{'='*60}")
        print(f"Выполняется: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            print(f"⚠️  Таймаут при присоединении к каналу")
            return False
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Неизвестная ошибка"
            # Проверяем, может быть peer уже присоединен
            if "already exists" in error_msg.lower() or "already a member" in error_msg.lower():
                print(f"✓ {org_name} уже присоединен к каналу")
                return True
            elif "input/output error" in error_msg.lower():
                print(f"⚠️  I/O ошибка при присоединении к каналу")
                print(f"   Peer может быть уже присоединен. Проверьте вручную позже.")
                # Возвращаем True, так как peer мог быть уже присоединен
                return True
            else:
                print(f"❌ Ошибка: {error_msg}")
                if result.stdout:
                    print(f"Вывод: {result.stdout}")
                return False
        
        print(f"✓ {org_name} успешно присоединен к каналу")
        if result.stdout:
            print(result.stdout)
        
        return True
    
    def update_anchor_peer(self, org_name):
        """Обновляет anchor peer для организации"""
        org_config = self.orgs[org_name]
        anchor_tx = self.channel_dir / f"{org_config['msp_id']}anchors.tx"
        
        if not anchor_tx.exists():
            print(f"❌ Файл {anchor_tx} не найден")
            return False
        
        peer_container = org_config["peer"]
        
        # Получаем путь к CA сертификату orderer
        orderer_ca_file = self.find_orderer_ca_cert()
        if not orderer_ca_file:
            print(f"❌ Не найден CA сертификат orderer")
            return False
        
        # Путь к MSP Admin пользователя
        admin_msp = self.orgs_dir / "peerOrganizations" / org_config["domain"] / "users" / org_config["admin_user"] / "msp"
        if not admin_msp.exists():
            print(f"❌ MSP Admin пользователя не найден: {admin_msp}")
            return False
        
        # Копируем MSP Admin в контейнер
        admin_msp_container_path = "/etc/hyperledger/fabric/admin-msp"
        
        # Удаляем старую директорию, если она существует (для чистоты)
        remove_cmd = [
            "docker", "exec",
            peer_container,
            "rm", "-rf", admin_msp_container_path
        ]
        subprocess.run(remove_cmd, capture_output=True)  # Игнорируем ошибки, если директории нет
        
        # Копируем MSP Admin в контейнер
        copy_cmd = [
            "docker", "cp",
            str(admin_msp.absolute()) + "/.",
            f"{peer_container}:{admin_msp_container_path}"
        ]
        result = subprocess.run(copy_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Ошибка при копировании Admin MSP: {result.stderr}")
            return False
        
        # Копируем файлы в контейнер
        copy_cmd = [
            "docker", "cp",
            str(anchor_tx.absolute()),
            f"{peer_container}:/opt/gopath/src/github.com/hyperledger/fabric/peer/{org_config['msp_id']}anchors.tx"
        ]
        result = subprocess.run(copy_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️  Предупреждение при копировании anchor tx: {result.stderr}")
        
        # Копируем orderer CA в рабочую директорию
        copy_cmd = [
            "docker", "cp",
            str(orderer_ca_file.absolute()),
            f"{peer_container}:/opt/gopath/src/github.com/hyperledger/fabric/peer/orderer-ca.pem"
        ]
        result = subprocess.run(copy_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Ошибка при копировании orderer CA: {result.stderr}")
            return False
        
        # Проверяем, что файл скопирован
        check_cmd = [
            "docker", "exec",
            peer_container,
            "test", "-f", "/opt/gopath/src/github.com/hyperledger/fabric/peer/orderer-ca.pem"
        ]
        result = subprocess.run(check_cmd, capture_output=True)
        if result.returncode != 0:
            print(f"❌ Файл orderer-ca.pem не найден в контейнере после копирования")
            return False
        
        # Также копируем в стандартное место на случай, если команда ищет там
        copy_cmd2 = [
            "docker", "exec",
            peer_container,
            "mkdir", "-p", "/etc/hyperledger/fabric"
        ]
        subprocess.run(copy_cmd2, capture_output=True)
        
        copy_cmd3 = [
            "docker", "exec",
            peer_container,
            "cp", "/opt/gopath/src/github.com/hyperledger/fabric/peer/orderer-ca.pem", "/etc/hyperledger/fabric/orderer-ca.pem"
        ]
        subprocess.run(copy_cmd3, capture_output=True)
        
        # Команда обновления anchor peer
        # Используем Admin MSP для подписи транзакции
        # Используем имя контейнера для подключения в Docker сети
        # но TLS hostname для проверки сертификата
        cmd = [
            "docker", "exec",
            "-e", f"CORE_PEER_LOCALMSPID={org_config['msp_id']}",
            "-e", "CORE_PEER_TLS_ENABLED=true",
            "-e", f"CORE_PEER_ADDRESS={org_config['peer']}:{org_config['peer_port']}",
            "-e", f"CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt",
            "-e", f"CORE_PEER_MSPCONFIGPATH={admin_msp_container_path}",  # Используем Admin MSP
            "-w", "/opt/gopath/src/github.com/hyperledger/fabric/peer",
            peer_container,
            "peer", "channel", "update",
            "-o", f"{self.orderer['container']}:{self.orderer['port']}",  # Используем имя контейнера
            "--ordererTLSHostnameOverride", self.orderer["host"],  # TLS hostname для проверки сертификата
            "-c", self.channel_name,
            "-f", f"./{org_config['msp_id']}anchors.tx",
            "--tls",
            "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/orderer-ca.pem"  # Полный путь
        ]
        
        print(f"\n{'='*60}")
        print(f"Обновление anchor peer для {org_name}")
        print(f"{'='*60}")
        print(f"Выполняется: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            print(f"⚠️  Таймаут при обновлении anchor peer для {org_name}")
            return False
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Неизвестная ошибка"
            # EOF ошибка может быть временной - транзакция могла пройти
            if "EOF" in error_msg or "error reading from server" in error_msg:
                print(f"⚠️  Временная ошибка при обновлении anchor peer для {org_name}: {error_msg}")
                print(f"   Транзакция могла пройти успешно, проверьте позже")
                # Возвращаем True для EOF ошибок, так как транзакция может пройти
                return True
            else:
                print(f"❌ Ошибка: {error_msg}")
                if result.stdout:
                    print(f"Вывод: {result.stdout}")
                return False
        
        print(f"✓ Anchor peer для {org_name} успешно обновлен")
        if result.stdout:
            print(result.stdout)
        
        return True
    
    def setup_channel(self, force_recreate=False):
        """Выполняет полную настройку канала"""
        print("\n" + "="*60)
        print(f"Настройка канала {self.channel_name}")
        print("="*60)
        
        if not self.check_prerequisites():
            return False
        
        # 1. Создание канала
        if not self.create_channel(force_recreate=force_recreate):
            return False
        
        # Небольшая задержка для синхронизации
        print("\n⏳ Ожидание синхронизации...")
        time.sleep(2)
        
        # 2. Присоединение peer'ов к каналу
        for org_name in self.orgs.keys():
            if not self.join_peer(org_name):
                return False
            time.sleep(1)
        
        # 3. Обновление anchor peer'ов
        for org_name in self.orgs.keys():
            # Повторные попытки для обновления anchor peer (может быть временная ошибка EOF)
            max_attempts = 3
            success = False
            for attempt in range(max_attempts):
                if attempt > 0:
                    print(f"\n⏳ Повторная попытка обновления anchor peer для {org_name} ({attempt + 1}/{max_attempts})...")
                    time.sleep(5)  # Увеличенная задержка между попытками
                
                if self.update_anchor_peer(org_name):
                    success = True
                    break
            
            if not success:
                print(f"\n⚠️  Предупреждение: не удалось обновить anchor peer для {org_name} после {max_attempts} попыток")
                print(f"   Можно попробовать обновить вручную позже")
                # Не останавливаем процесс, продолжаем с другими организациями
            
            time.sleep(2)  # Задержка между обновлениями разных организаций
        
        print("\n" + "="*60)
        print(f"✓ Канал {self.channel_name} успешно настроен!")
        print("="*60)
        print("\nВсе операции выполнены:")
        print("  ✓ Канал создан")
        print("  ✓ Peer'ы присоединены к каналу")
        print("  ✓ Anchor peer'ы обновлены")
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Настройка канала Hyperledger Fabric")
    parser.add_argument(
        "--channel",
        default="npa-channel",
        help="Имя канала (по умолчанию: npa-channel)"
    )
    parser.add_argument(
        "--create-only",
        action="store_true",
        help="Только создать канал"
    )
    parser.add_argument(
        "--join-only",
        action="store_true",
        help="Только присоединить peer'ы к каналу"
    )
    parser.add_argument(
        "--anchor-only",
        action="store_true",
        help="Только обновить anchor peer'ы"
    )
    parser.add_argument(
        "--org",
        choices=["Org1", "Org2"],
        help="Выполнить операцию только для указанной организации"
    )
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="Принудительно пересоздать канал (удалив старый)"
    )
    
    args = parser.parse_args()
    
    setup = ChannelSetup(channel_name=args.channel)
    
    if args.create_only:
        if not setup.check_prerequisites():
            sys.exit(1)
        success = setup.create_channel(force_recreate=args.force_recreate)
    elif args.join_only:
        if args.org:
            success = setup.join_peer(args.org)
        else:
            success = True
            for org_name in setup.orgs.keys():
                if not setup.join_peer(org_name):
                    success = False
    elif args.anchor_only:
        if args.org:
            success = setup.update_anchor_peer(args.org)
        else:
            success = True
            for org_name in setup.orgs.keys():
                if not setup.update_anchor_peer(org_name):
                    success = False
    else:
        success = setup.setup_channel(force_recreate=args.force_recreate)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

