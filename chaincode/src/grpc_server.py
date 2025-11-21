#!/usr/bin/env python3
"""
gRPC сервер для external chaincode
Обрабатывает запросы от peer через gRPC
"""

import grpc
import logging
import json
from concurrent import futures
from typing import Dict, Any

# Для external chaincode нужно использовать protobuf определения из Fabric
# В упрощенной версии используем базовый подход

logger = logging.getLogger(__name__)


class ChaincodeStub:
    """Упрощенная заглушка для ChaincodeStubInterface"""
    
    def __init__(self, channel_id: str, tx_id: str):
        self.channel_id = channel_id
        self.tx_id = tx_id
        self.state = {}  # В реальности это будет обращение к ledger через peer
    
    def get_state(self, key: str) -> bytes:
        """Получить состояние из ledger"""
        # В реальной реализации это будет gRPC вызов к peer
        # Здесь упрощенная версия для демонстрации
        value = self.state.get(key)
        if value:
            return value.encode('utf-8') if isinstance(value, str) else value
        return b''
    
    def put_state(self, key: str, value: bytes) -> None:
        """Сохранить состояние в ledger"""
        # В реальной реализации это будет gRPC вызов к peer
        self.state[key] = value.decode('utf-8') if isinstance(value, bytes) else value
    
    def create_composite_key(self, object_type: str, attributes: list) -> str:
        """Создать составной ключ"""
        return f"{object_type}:{':'.join(attributes)}"


class ChaincodeServer:
    """gRPC сервер для external chaincode"""
    
    def __init__(self, port: int = 9999):
        self.port = port
        self.server = None
    
    def start(self):
        """Запустить gRPC сервер"""
        # В реальной реализации здесь будет настройка gRPC сервера
        # с использованием protobuf определений из Hyperledger Fabric
        logger.info(f"gRPC сервер chaincode запущен на порту {self.port}")
        logger.warning("Это упрощенная версия. Для production используйте официальные protobuf определения Fabric")
    
    def stop(self):
        """Остановить gRPC сервер"""
        if self.server:
            self.server.stop(0)
            logger.info("gRPC сервер остановлен")
    
    def process_invoke(self, channel_id: str, tx_id: str, function: str, args: list) -> Dict[str, Any]:
        """
        Обработать вызов chaincode
        
        Args:
            channel_id: ID канала
            tx_id: ID транзакции
            function: Имя функции
            args: Аргументы
        
        Returns:
            Результат выполнения
        """
        from chaincode import invoke_chaincode
        
        stub = ChaincodeStub(channel_id, tx_id)
        result_bytes = invoke_chaincode(stub, function, args)
        result = json.loads(result_bytes.decode('utf-8'))
        return result


def main():
    """Главная функция для запуска gRPC сервера"""
    import os
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    port = int(os.getenv('CHAINCODE_SERVER_PORT', '9999'))
    
    server = ChaincodeServer(port)
    try:
        server.start()
        # В реальной реализации здесь будет бесконечный цикл ожидания
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
        server.stop()


if __name__ == '__main__':
    main()

