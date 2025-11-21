#!/usr/bin/env python3
"""
Альтернативный скрипт для генерации криптографических материалов
Использует Docker образы Hyperledger Fabric для генерации
"""

import subprocess
import os
from pathlib import Path


class CryptoMaterialGenerator:
    def __init__(self, base_dir="."):
        self.base_dir = Path(base_dir)
        self.config_dir = self.base_dir / "config"
        self.orgs_dir = self.base_dir / "organizations"
        self.channel_dir = self.base_dir / "channel-artifacts"
        
    def run_docker_command(self, cmd, description):
        """Выполняет команду через Docker"""
        print(f"\n{'='*60}")
        print(f"{description}")
        print(f"{'='*60}")
        print(f"Выполняется: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=self.base_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Ошибка: {result.stderr}")
            return False
        else:
            print(f"✓ Успешно: {result.stdout}")
            return True
    
    def generate_crypto_materials(self):
        """Генерирует криптографические материалы используя Docker"""
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{self.base_dir.absolute()}:/data",
            "-w", "/data",
            "hyperledger/fabric-tools:2.5",
            "cryptogen", "generate",
            "--config=./config/crypto-config.yaml",
            "--output=./organizations"
        ]
        return self.run_docker_command(cmd, "Генерация криптографических материалов")
    
    def generate_genesis_block(self):
        """Генерирует genesis блок"""
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{self.base_dir.absolute()}:/data",
            "-w", "/data",
            "-e", "FABRIC_CFG_PATH=/data/config",
            "hyperledger/fabric-tools:2.5",
            "configtxgen",
            "-profile", "TwoOrgsOrdererGenesis",
            "-channelID", "system-channel",
            "-outputBlock", "./channel-artifacts/genesis.block"
        ]
        return self.run_docker_command(cmd, "Генерация genesis блока")
    
    def generate_channel_tx(self, channel_name="npa-channel"):
        """Генерирует транзакцию создания канала"""
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{self.base_dir.absolute()}:/data",
            "-w", "/data",
            "-e", "FABRIC_CFG_PATH=/data/config",
            "hyperledger/fabric-tools:2.5",
            "configtxgen",
            "-profile", "TwoOrgsChannel",
            "-channelID", channel_name,
            "-outputCreateChannelTx", f"./channel-artifacts/{channel_name}.tx"
        ]
        return self.run_docker_command(cmd, f"Генерация транзакции создания канала {channel_name}")
    
    def generate_anchor_peers(self, org_name, channel_name="npa-channel"):
        """Генерирует транзакцию обновления anchor peer"""
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{self.base_dir.absolute()}:/data",
            "-w", "/data",
            "-e", "FABRIC_CFG_PATH=/data/config",
            "hyperledger/fabric-tools:2.5",
            "configtxgen",
            "-profile", "TwoOrgsChannel",
            "-outputAnchorPeersUpdate", f"./channel-artifacts/{org_name}anchors.tx",
            "-channelID", channel_name,
            "-asOrg", org_name
        ]
        return self.run_docker_command(
            cmd,
            f"Генерация транзакции anchor peer для {org_name}"
        )
    
    def generate_all(self, channel_name="npa-channel"):
        """Генерирует все необходимые артефакты"""
        print("\n" + "="*60)
        print("Генерация криптографических материалов и артефактов канала")
        print("="*60)
        
        # Проверка наличия Docker
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Docker не найден. Убедитесь, что Docker установлен и запущен.")
            return False
        
        # Проверка наличия конфигурационных файлов
        if not (self.config_dir / "crypto-config.yaml").exists():
            print("❌ Файл config/crypto-config.yaml не найден.")
            print("   Сначала запустите: python generate_fabric_config.py")
            return False
        
        if not (self.config_dir / "configtx.yaml").exists():
            print("❌ Файл config/configtx.yaml не найден.")
            print("   Сначала запустите: python generate_fabric_config.py")
            return False
        
        success = True
        
        # Генерация криптографических материалов
        if not self.generate_crypto_materials():
            success = False
        
        # Генерация genesis блока
        if not self.generate_genesis_block():
            success = False
        
        # Генерация транзакции создания канала
        if not self.generate_channel_tx(channel_name):
            success = False
        
        # Генерация anchor peer транзакций
        if not self.generate_anchor_peers("Org1MSP", channel_name):
            success = False
        
        if not self.generate_anchor_peers("Org2MSP", channel_name):
            success = False
        
        if success:
            print("\n" + "="*60)
            print("✓ Все артефакты успешно сгенерированы!")
            print("="*60)
            print("\nТеперь вы можете запустить сеть:")
            print("  docker-compose up -d")
        else:
            print("\n" + "="*60)
            print("❌ Произошли ошибки при генерации")
            print("="*60)
        
        return success


def main():
    import sys
    channel_name = sys.argv[1] if len(sys.argv) > 1 else "npa-channel"
    
    generator = CryptoMaterialGenerator()
    generator.generate_all(channel_name)


if __name__ == "__main__":
    main()

