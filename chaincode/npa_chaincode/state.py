#!/usr/bin/env python3
"""
state.py - Управление состоянием в Hyperledger Fabric ledger

Назначение:
    Этот модуль отвечает за все операции работы с состоянием (state) в ledger:
    - Получение данных из ledger
    - Сохранение данных в ledger
    - Создание составных ключей
    - Работа с историей транзакций
    - Удаление данных (если необходимо)
"""

import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class StateManager:
    """
    Менеджер состояния для работы с Hyperledger Fabric ledger
    
    Инкапсулирует всю логику работы с состоянием, предоставляя
    высокоуровневый интерфейс для чтения и записи данных.
    """
    
    def __init__(self, stub):
        """
        Инициализация менеджера состояния
        
        Args:
            stub: ChaincodeStubInterface для взаимодействия с ledger
        """
        self.stub = stub
    
    def get_state(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Получить значение из ledger по ключу
        
        Args:
            key: Ключ для поиска в ledger
        
        Returns:
            Словарь с данными или None, если ключ не найден
        """
        try:
            state_bytes = self.stub.get_state(key)
            if not state_bytes or len(state_bytes) == 0:
                logger.debug(f"Ключ {key} не найден в ledger")
                return None
            
            state_dict = json.loads(state_bytes.decode('utf-8'))
            logger.debug(f"Получено состояние для ключа {key}")
            return state_dict
        
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON для ключа {key}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении состояния для ключа {key}: {str(e)}")
            return None
    
    def put_state(self, key: str, value: Dict[str, Any]) -> bool:
        """
        Сохранить значение в ledger
        
        Args:
            key: Ключ для сохранения
            value: Словарь с данными для сохранения
        
        Returns:
            True если успешно, False в случае ошибки
        """
        try:
            value_json = json.dumps(value, ensure_ascii=False)
            value_bytes = value_json.encode('utf-8')
            self.stub.put_state(key, value_bytes)
            logger.debug(f"Состояние сохранено для ключа {key}")
            return True
        
        except Exception as e:
            logger.error(f"Ошибка при сохранении состояния для ключа {key}: {str(e)}")
            return False
    
    def delete_state(self, key: str) -> bool:
        """
        Удалить значение из ledger
        
        Args:
            key: Ключ для удаления
        
        Returns:
            True если успешно, False в случае ошибки
        """
        try:
            self.stub.del_state(key)
            logger.debug(f"Состояние удалено для ключа {key}")
            return True
        
        except Exception as e:
            logger.error(f"Ошибка при удалении состояния для ключа {key}: {str(e)}")
            return False
    
    def get_state_by_range(self, start_key: str, end_key: str) -> List[Dict[str, Any]]:
        """
        Получить диапазон значений из ledger
        
        Args:
            start_key: Начальный ключ (включительно)
            end_key: Конечный ключ (исключительно)
        
        Returns:
            Список словарей с данными
        """
        try:
            results = []
            iterator = self.stub.get_state_by_range(start_key, end_key)
            
            for result in iterator:
                try:
                    value = json.loads(result.value.decode('utf-8'))
                    results.append({
                        "key": result.key,
                        "value": value
                    })
                except json.JSONDecodeError as e:
                    logger.warning(f"Ошибка декодирования для ключа {result.key}: {str(e)}")
            
            iterator.close()
            logger.debug(f"Получено {len(results)} записей в диапазоне {start_key}-{end_key}")
            return results
        
        except Exception as e:
            logger.error(f"Ошибка при получении диапазона {start_key}-{end_key}: {str(e)}")
            return []
    
    def create_composite_key(self, object_type: str, attributes: List[str]) -> str:
        """
        Создать составной ключ для организации данных
        
        Args:
            object_type: Тип объекта (например, "TASK", "DOCUMENT")
            attributes: Список атрибутов для ключа
        
        Returns:
            Составной ключ
        """
        try:
            composite_key = self.stub.create_composite_key(object_type, attributes)
            logger.debug(f"Создан составной ключ: {composite_key}")
            return composite_key
        except Exception as e:
            logger.error(f"Ошибка при создании составного ключа: {str(e)}")
            # Fallback на простой ключ
            return f"{object_type}:{':'.join(attributes)}"
    
    def get_state_by_partial_composite_key(self, object_type: str, attributes: List[str]) -> List[Dict[str, Any]]:
        """
        Получить значения по частичному составному ключу
        
        Args:
            object_type: Тип объекта
            attributes: Частичный список атрибутов
        
        Returns:
            Список словарей с данными
        """
        try:
            results = []
            iterator = self.stub.get_state_by_partial_composite_key(object_type, attributes)
            
            for result in iterator:
                try:
                    value = json.loads(result.value.decode('utf-8'))
                    results.append({
                        "key": result.key,
                        "value": value
                    })
                except json.JSONDecodeError as e:
                    logger.warning(f"Ошибка декодирования для ключа {result.key}: {str(e)}")
            
            iterator.close()
            logger.debug(f"Получено {len(results)} записей для типа {object_type}")
            return results
        
        except Exception as e:
            logger.error(f"Ошибка при получении частичного ключа: {str(e)}")
            return []
    
    def get_history_for_key(self, key: str) -> List[Dict[str, Any]]:
        """
        Получить историю изменений для ключа
        
        Args:
            key: Ключ для получения истории
        
        Returns:
            Список словарей с историей изменений
        """
        try:
            history = []
            iterator = self.stub.get_history_for_key(key)
            
            for result in iterator:
                try:
                    value = json.loads(result.value.decode('utf-8')) if result.value else None
                    history.append({
                        "tx_id": result.tx_id,
                        "timestamp": result.timestamp,
                        "is_delete": result.is_delete,
                        "value": value
                    })
                except json.JSONDecodeError as e:
                    logger.warning(f"Ошибка декодирования истории для ключа {key}: {str(e)}")
            
            iterator.close()
            logger.debug(f"Получена история из {len(history)} записей для ключа {key}")
            return history
        
        except Exception as e:
            logger.error(f"Ошибка при получении истории для ключа {key}: {str(e)}")
            return []

