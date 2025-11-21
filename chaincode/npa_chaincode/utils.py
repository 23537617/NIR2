#!/usr/bin/env python3
"""
utils.py - Вспомогательные функции и утилиты

Назначение:
    Этот модуль содержит вспомогательные функции для chaincode:
    - Валидация данных
    - Форматирование ответов
    - Константы и настройки
    - Вспомогательные функции для работы с данными
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


# Константы для статусов задач
TASK_STATUS_CREATED = "CREATED"
TASK_STATUS_IN_PROGRESS = "IN_PROGRESS"
TASK_STATUS_COMPLETED = "COMPLETED"
TASK_STATUS_CANCELLED = "CANCELLED"

VALID_TASK_STATUSES = [
    TASK_STATUS_CREATED,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_COMPLETED,
    TASK_STATUS_CANCELLED
]

# Префиксы для ключей
KEY_PREFIX_TASK = "TASK"
KEY_PREFIX_DOCUMENT = "DOC"


def validate_status(status: str) -> bool:
    """
    Валидация статуса задачи
    
    Args:
        status: Статус для проверки
    
    Returns:
        True если статус валиден, False иначе
    """
    return status in VALID_TASK_STATUSES


def format_response(success: bool, data: Any = None, error: Optional[str] = None) -> Dict[str, Any]:
    """
    Форматирование стандартного ответа chaincode
    
    Args:
        success: Успешность операции
        data: Данные для возврата
        error: Сообщение об ошибке (если есть)
    
    Returns:
        Словарь с отформатированным ответом
    """
    response = {
        "success": success,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if success:
        if data is not None:
            response["data"] = data
    else:
        response["error"] = error or "Неизвестная ошибка"
    
    return response


def validate_task_data(task_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Валидация данных задачи
    
    Args:
        task_data: Словарь с данными задачи
    
    Returns:
        Кортеж (валидность, сообщение об ошибке)
    """
    required_fields = ["task_id", "title", "description", "assignee", "creator"]
    
    for field in required_fields:
        if field not in task_data:
            return False, f"Отсутствует обязательное поле: {field}"
        
        if not task_data[field] or not str(task_data[field]).strip():
            return False, f"Поле {field} не может быть пустым"
    
    # Валидация task_id (должен быть непустой строкой)
    if not isinstance(task_data["task_id"], str):
        return False, "task_id должен быть строкой"
    
    return True, None


def validate_document_version_data(version_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Валидация данных версии документа
    
    Args:
        version_data: Словарь с данными версии документа
    
    Returns:
        Кортеж (валидность, сообщение об ошибке)
    """
    required_fields = ["version", "content_hash", "uploaded_by"]
    
    for field in required_fields:
        if field not in version_data:
            return False, f"Отсутствует обязательное поле: {field}"
        
        if not version_data[field] or not str(version_data[field]).strip():
            return False, f"Поле {field} не может быть пустым"
    
    # Валидация версии (должна быть строкой в формате X.Y)
    version = str(version_data["version"]).strip()
    if not version:
        return False, "version не может быть пустым"
    
    # Валидация content_hash (должен быть непустой строкой)
    if not isinstance(version_data["content_hash"], str):
        return False, "content_hash должен быть строкой"
    
    return True, None


def create_task_key(task_id: str) -> str:
    """
    Создать ключ для задачи
    
    Args:
        task_id: Идентификатор задачи
    
    Returns:
        Ключ для сохранения в ledger
    """
    return f"{KEY_PREFIX_TASK}_{task_id}"


def create_document_key(task_id: str, document_id: str) -> str:
    """
    Создать ключ для документа
    
    Args:
        task_id: Идентификатор задачи
        document_id: Идентификатор документа
    
    Returns:
        Ключ для сохранения в ledger
    """
    return f"{KEY_PREFIX_DOCUMENT}_{task_id}_{document_id}"


def parse_metadata(metadata_str: Optional[str]) -> Dict[str, Any]:
    """
    Парсинг метаданных из строки JSON
    
    Args:
        metadata_str: Строка с JSON метаданными
    
    Returns:
        Словарь с метаданными или пустой словарь
    """
    if not metadata_str:
        return {}
    
    try:
        if isinstance(metadata_str, str):
            return json.loads(metadata_str)
        elif isinstance(metadata_str, dict):
            return metadata_str
        else:
            return {}
    except json.JSONDecodeError as e:
        logger.warning(f"Ошибка парсинга метаданных: {str(e)}")
        return {}


def sanitize_string(value: Any, max_length: Optional[int] = None) -> str:
    """
    Очистка и валидация строкового значения
    
    Args:
        value: Значение для очистки
        max_length: Максимальная длина (если указана)
    
    Returns:
        Очищенная строка
    """
    if value is None:
        return ""
    
    string_value = str(value).strip()
    
    if max_length and len(string_value) > max_length:
        logger.warning(f"Строка обрезана с {len(string_value)} до {max_length} символов")
        return string_value[:max_length]
    
    return string_value


def get_current_timestamp() -> str:
    """
    Получить текущую временную метку в ISO формате
    
    Returns:
        Строка с временной меткой
    """
    return datetime.utcnow().isoformat()


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Объединение словарей (последний имеет приоритет)
    
    Args:
        *dicts: Словари для объединения
    
    Returns:
        Объединенный словарь
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result

