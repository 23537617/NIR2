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
        
        # Проверка запущенных контейнеров
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True
            )
            running_containers = result.stdout.strip().split('\n')
            
            required_containers = [
                "orderer0",
                "peer0.org1.example.com",
                "peer0.org2.example.com"
            ]
            
            for container in required_containers:
                if container in running_containers:
                    print(f"✓ Контейнер {container} запущен")
                else:
                    print(f"❌ Контейнер {container} не запущен")
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
        orderer_ca = self.orgs_dir / "ordererOrganizations" / self.orderer["domain"] / "orderers" / self.orderer["host"] / "msp" / "tlscacerts"
        
        # Находим файл CA сертификата orderer
        orderer_ca_files = list(orderer_ca.glob("*.pem"))
        if not orderer_ca_files:
            print(f"❌ Не найден CA сертификат orderer в {orderer_ca}")
            return False
        orderer_ca_file = orderer_ca_files[0]
        
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
    
    def create_channel(self):
        """Создает канал (от имени Org1)"""
        org_name = "Org1"
        org_config = self.orgs[org_name]
        
        channel_tx = self.channel_dir / f"{self.channel_name}.tx"
        channel_block = self.channel_dir / f"{self.channel_name}.block"
        
        # Проверяем, не существует ли уже канал
        if channel_block.exists():
            response = input(f"⚠️  Файл {channel_block} уже существует. Пересоздать? (y/n): ")
            if response.lower() != 'y':
                print("Пропущено создание канала")
                return True
        
        # Получаем пути к сертификатам
        orderer_ca = self.orgs_dir / "ordererOrganizations" / self.orderer["domain"] / "orderers" / self.orderer["host"] / "msp" / "tlscacerts"
        orderer_ca_files = list(orderer_ca.glob("*.pem"))
        if not orderer_ca_files:
            print(f"❌ Не найден CA сертификат orderer")
            return False
        orderer_ca_file = orderer_ca_files[0]
        
        # Копируем файлы в контейнер
        peer_container = org_config["peer"]
        
        # Копируем channel tx в контейнер
        copy_cmd = [
            "docker", "cp",
            str(channel_tx.absolute()),
            f"{peer_container}:/opt/gopath/src/github.com/hyperledger/fabric/peer/{self.channel_name}.tx"
        ]
        subprocess.run(copy_cmd, capture_output=True)
        
        # Копируем orderer CA в контейнер
        copy_cmd = [
            "docker", "cp",
            str(orderer_ca_file.absolute()),
            f"{peer_container}:/opt/gopath/src/github.com/hyperledger/fabric/peer/orderer-ca.pem"
        ]
        subprocess.run(copy_cmd, capture_output=True)
        
        # Команда создания канала
        cmd = [
            "docker", "exec",
            "-e", f"CORE_PEER_LOCALMSPID={org_config['msp_id']}",
            "-e", "CORE_PEER_TLS_ENABLED=true",
            "-e", f"CORE_PEER_ADDRESS={org_config['peer']}:{org_config['peer_port']}",
            "-e", f"CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt",
            "-e", f"CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/msp",
            "-w", "/opt/gopath/src/github.com/hyperledger/fabric/peer",
            peer_container,
            "peer", "channel", "create",
            "-o", f"{self.orderer['host']}:{self.orderer['port']}",
            "-c", self.channel_name,
            "--ordererTLSHostnameOverride", self.orderer["host"],
            "-f", f"./{self.channel_name}.tx",
            "--outputBlock", f"./{self.channel_name}.block",
            "--tls",
            "--cafile", "./orderer-ca.pem"
        ]
        
        print(f"\n{'='*60}")
        print(f"Создание канала {self.channel_name}")
        print(f"{'='*60}")
        print(f"Выполняется: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Ошибка: {result.stderr}")
            if result.stdout:
                print(f"Вывод: {result.stdout}")
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
        
        # Копируем блок канала в контейнер
        copy_cmd = [
            "docker", "cp",
            str(channel_block.absolute()),
            f"{peer_container}:/opt/gopath/src/github.com/hyperledger/fabric/peer/{self.channel_name}.block"
        ]
        subprocess.run(copy_cmd, capture_output=True)
        
        # Команда присоединения к каналу
        cmd = [
            "docker", "exec",
            "-e", f"CORE_PEER_LOCALMSPID={org_config['msp_id']}",
            "-e", "CORE_PEER_TLS_ENABLED=true",
            "-e", f"CORE_PEER_ADDRESS={org_config['peer']}:{org_config['peer_port']}",
            "-e", f"CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt",
            "-e", f"CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/msp",
            "-w", "/opt/gopath/src/github.com/hyperledger/fabric/peer",
            peer_container,
            "peer", "channel", "join",
            "-b", f"./{self.channel_name}.block"
        ]
        
        print(f"\n{'='*60}")
        print(f"Присоединение {org_name} к каналу {self.channel_name}")
        print(f"{'='*60}")
        print(f"Выполняется: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Ошибка: {result.stderr}")
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
        
        # Получаем пути к сертификатам
        orderer_ca = self.orgs_dir / "ordererOrganizations" / self.orderer["domain"] / "orderers" / self.orderer["host"] / "msp" / "tlscacerts"
        orderer_ca_files = list(orderer_ca.glob("*.pem"))
        if not orderer_ca_files:
            print(f"❌ Не найден CA сертификат orderer")
            return False
        orderer_ca_file = orderer_ca_files[0]
        
        # Копируем файлы в контейнер
        copy_cmd = [
            "docker", "cp",
            str(anchor_tx.absolute()),
            f"{peer_container}:/opt/gopath/src/github.com/hyperledger/fabric/peer/{org_config['msp_id']}anchors.tx"
        ]
        subprocess.run(copy_cmd, capture_output=True)
        
        copy_cmd = [
            "docker", "cp",
            str(orderer_ca_file.absolute()),
            f"{peer_container}:/opt/gopath/src/github.com/hyperledger/fabric/peer/orderer-ca.pem"
        ]
        subprocess.run(copy_cmd, capture_output=True)
        
        # Команда обновления anchor peer
        cmd = [
            "docker", "exec",
            "-e", f"CORE_PEER_LOCALMSPID={org_config['msp_id']}",
            "-e", "CORE_PEER_TLS_ENABLED=true",
            "-e", f"CORE_PEER_ADDRESS={org_config['peer']}:{org_config['peer_port']}",
            "-e", f"CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt",
            "-e", f"CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/msp",
            "-w", "/opt/gopath/src/github.com/hyperledger/fabric/peer",
            peer_container,
            "peer", "channel", "update",
            "-o", f"{self.orderer['host']}:{self.orderer['port']}",
            "--ordererTLSHostnameOverride", self.orderer["host"],
            "-c", self.channel_name,
            "-f", f"./{org_config['msp_id']}anchors.tx",
            "--tls",
            "--cafile", "./orderer-ca.pem"
        ]
        
        print(f"\n{'='*60}")
        print(f"Обновление anchor peer для {org_name}")
        print(f"{'='*60}")
        print(f"Выполняется: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Ошибка: {result.stderr}")
            if result.stdout:
                print(f"Вывод: {result.stdout}")
            return False
        
        print(f"✓ Anchor peer для {org_name} успешно обновлен")
        if result.stdout:
            print(result.stdout)
        
        return True
    
    def setup_channel(self):
        """Выполняет полную настройку канала"""
        print("\n" + "="*60)
        print(f"Настройка канала {self.channel_name}")
        print("="*60)
        
        if not self.check_prerequisites():
            return False
        
        # 1. Создание канала
        if not self.create_channel():
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
            if not self.update_anchor_peer(org_name):
                return False
            time.sleep(1)
        
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
    
    args = parser.parse_args()
    
    setup = ChannelSetup(channel_name=args.channel)
    
    if args.create_only:
        if not setup.check_prerequisites():
            sys.exit(1)
        success = setup.create_channel()
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
        success = setup.setup_channel()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

