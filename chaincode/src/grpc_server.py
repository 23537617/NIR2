import os
import sys
import logging
from fabric_chaincode_python.shim.shim import start

# Добавляем корневую директорию проекта в sys.path для корректного импорта npa_chaincode
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from npa_chaincode.chaincode import NPAChaincode

def main():
    """Главная функция для запуска chaincode сервера"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Запускаем чейнкод
    # Для внешнего чейнкода (CCAAS) SDK автоматически считывает 
    # CHAINCODE_SERVER_ADDRESS или запускает прослушивание на порту
    logger = logging.getLogger(__name__)
    logger.info("Запуск NPA Chaincode через официальный SDK...")
    
    chaincode = NPAChaincode()
    start(chaincode)

if __name__ == '__main__':
    main()

