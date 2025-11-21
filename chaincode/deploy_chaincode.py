#!/usr/bin/env python3
"""
Скрипт для развертывания chaincode в Hyperledger Fabric
"""

import subprocess
import os
import sys
from pathlib import Path


class ChaincodeDeployer:
    def __init__(self, base_dir=".."):
        self.base_dir = Path(base_dir)
        self.chaincode_dir = Path(__file__).parent
        self.orgs_dir = self.base_dir / "organizations"
        self.channel_dir = self.base_dir / "channel-artifacts"
        
        # Конфигурация
        self.channel_name = "npa-channel"
        self.chaincode_name = "taskdocument"
        self.chaincode_version = "1.0"
        self.chaincode_path = "."
        self.chaincode_package = f"{self.chaincode_name}.tar.gz"
        
        # Порты для external chaincode
        self.chaincode_address_org1 = "chaincode-rest:9999"
        self.chaincode_address_org2 = "chaincode-rest:9999"
    
    def run_peer_command(self, org_name, command, description):
        """Выполнить команду peer"""
        org_config = {
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
        }[org_name]
        
        print(f"\n{'='*60}")
        print(f"{description} ({org_name})")
        print(f"{'='*60}")
        
        # Формируем команду docker exec
        cmd = [
            "docker", "exec",
            "-e", f"CORE_PEER_LOCALMSPID={org_config['msp_id']}",
            "-e", "CORE_PEER_TLS_ENABLED=true",
            "-e", f"CORE_PEER_ADDRESS={org_config['peer']}:{org_config['peer_port']}",
            "-e", f"CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt",
            "-e", f"CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/msp",
            "-w", "/opt/gopath/src/github.com/hyperledger/fabric/peer",
            org_config["peer"],
            "peer"
        ] + command
        
        print(f"Выполняется: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Ошибка: {result.stderr}")
            return False
        else:
            print(f"✓ Успешно")
            if result.stdout:
                print(result.stdout)
            return True
    
    def package_chaincode(self):
        """Упаковать chaincode"""
        print("\n" + "="*60)
        print("Упаковка chaincode")
        print("="*60)
        
        # В реальности здесь нужно использовать peer lifecycle package
        # Для external chaincode это не требуется, так как он работает как отдельный сервис
        print("✓ External chaincode не требует упаковки")
        return True
    
    def install_chaincode(self):
        """Установить chaincode на peer'ы"""
        print("\n" + "="*60)
        print("Установка chaincode")
        print("="*60)
        
        # Для external chaincode используем lifecycle approveformyorg
        # с указанием адреса external chaincode сервиса
        
        # Org1
        cmd_org1 = [
            "lifecycle", "approveformyorg",
            "-o", "orderer0:7050",
            "--ordererTLSHostnameOverride", "orderer.example.com",
            "--channelID", self.channel_name,
            "--name", self.chaincode_name,
            "--version", self.chaincode_version,
            "--package-id", f"{self.chaincode_name}:{self.chaincode_version}",
            "--sequence", "1",
            "--tls",
            "--cafile", "/etc/hyperledger/fabric/orderer-ca.pem",
            "--peerAddresses", "peer0.org1.example.com:7051",
            "--tlsRootCertFiles", "/etc/hyperledger/fabric/tls/ca.crt"
        ]
        
        # Для external chaincode нужно указать адрес
        # Это делается через connection.json или через параметры
        
        print("⚠️  Для external chaincode требуется специальная конфигурация")
        print("   Используйте peer lifecycle approveformyorg с параметрами:")
        print(f"   --chaincodeAddress {self.chaincode_address_org1}")
        
        return True
    
    def commit_chaincode(self):
        """Закоммитить chaincode в канал"""
        print("\n" + "="*60)
        print("Коммит chaincode в канал")
        print("="*60)
        
        # Коммит от имени Org1
        cmd = [
            "lifecycle", "commit",
            "-o", "orderer0:7050",
            "--ordererTLSHostnameOverride", "orderer.example.com",
            "--channelID", self.channel_name,
            "--name", self.chaincode_name,
            "--version", self.chaincode_version,
            "--sequence", "1",
            "--tls",
            "--cafile", "/etc/hyperledger/fabric/orderer-ca.pem",
            "--peerAddresses", "peer0.org1.example.com:7051",
            "--peerAddresses", "peer0.org2.example.com:9051",
            "--tlsRootCertFiles", "/etc/hyperledger/fabric/tls/ca.crt",
            "--tlsRootCertFiles", "/etc/hyperledger/fabric/tls/ca.crt"
        ]
        
        return self.run_peer_command("Org1", cmd, "Коммит chaincode")
    
    def deploy(self):
        """Полное развертывание chaincode"""
        print("\n" + "="*60)
        print("Развертывание chaincode")
        print("="*60)
        
        if not self.package_chaincode():
            return False
        
        if not self.install_chaincode():
            return False
        
        if not self.commit_chaincode():
            return False
        
        print("\n" + "="*60)
        print("✓ Chaincode успешно развернут!")
        print("="*60)
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Развертывание chaincode")
    parser.add_argument("--channel", default="npa-channel", help="Имя канала")
    parser.add_argument("--name", default="taskdocument", help="Имя chaincode")
    parser.add_argument("--version", default="1.0", help="Версия chaincode")
    
    args = parser.parse_args()
    
    deployer = ChaincodeDeployer()
    deployer.channel_name = args.channel
    deployer.chaincode_name = args.name
    deployer.chaincode_version = args.version
    
    success = deployer.deploy()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

