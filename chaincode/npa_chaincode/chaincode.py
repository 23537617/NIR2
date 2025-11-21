#!/usr/bin/env python3
"""
chaincode.py - Основной модуль NPA Chaincode

Назначение:
    Этот файл содержит основную бизнес-логику chaincode:
    - Определение класса NPAChaincode с методами для работы с задачами и документами
    - Реализация функций: createTask, updateTaskStatus, addDocumentVersion, getDocumentVersions
    - Обработка вызовов chaincode и маршрутизация к соответствующим методам
    - Интеграция с StateManager для работы с ledger
    - Использование утилит из utils для валидации и форматирования
"""

import logging
from typing import Dict, Any, List, Optional

from .state import StateManager
from .utils import (
    validate_status,
    format_response,
    validate_task_data,
    validate_document_version_data,
    create_task_key,
    get_current_timestamp,
    parse_metadata,
    sanitize_string,
    TASK_STATUS_CREATED
)

logger = logging.getLogger(__name__)


class NPAChaincode:
    """
    Основной класс NPA Chaincode для управления задачами и версиями документов
    
    Использует StateManager для работы с ledger и утилиты для валидации данных.
    """
    
    def __init__(self, stub):
        """
        Инициализация chaincode
        
        Args:
            stub: ChaincodeStubInterface для взаимодействия с ledger
        """
        self.state = StateManager(stub)
        logger.info("NPA Chaincode инициализирован")
    
    def create_task(self, task_id: str, title: str, description: str, 
                   assignee: str, creator: str) -> Dict[str, Any]:
        """
        Создать новую задачу
        
        Args:
            task_id: Уникальный идентификатор задачи
            title: Название задачи
            description: Описание задачи
            assignee: Исполнитель задачи
            creator: Создатель задачи
        
        Returns:
            Словарь с результатом операции
        """
        try:
            # Валидация входных данных
            task_data = {
                "task_id": task_id,
                "title": title,
                "description": description,
                "assignee": assignee,
                "creator": creator
            }
            
            is_valid, error_msg = validate_task_data(task_data)
            if not is_valid:
                return format_response(False, error=error_msg)
            
            # Очистка строковых значений
            task_id = sanitize_string(task_id)
            title = sanitize_string(title)
            description = sanitize_string(description)
            assignee = sanitize_string(assignee)
            creator = sanitize_string(creator)
            
            # Проверяем, не существует ли уже задача с таким ID
            task_key = create_task_key(task_id)
            existing_task = self.state.get_state(task_key)
            
            if existing_task:
                return format_response(
                    False,
                    error=f"Задача с ID {task_id} уже существует"
                )
            
            # Создаем новую задачу
            task = {
                "task_id": task_id,
                "title": title,
                "description": description,
                "assignee": assignee,
                "creator": creator,
                "status": TASK_STATUS_CREATED,
                "created_at": get_current_timestamp(),
                "updated_at": get_current_timestamp(),
                "documents": []
            }
            
            # Сохраняем задачу
            if self.state.put_state(task_key, task):
                logger.info(f"Задача {task_id} успешно создана")
                return format_response(True, data={"task": task})
            else:
                return format_response(
                    False,
                    error="Не удалось сохранить задачу в ledger"
                )
        
        except Exception as e:
            logger.error(f"Ошибка при создании задачи: {str(e)}")
            return format_response(False, error=str(e))
    
    def update_task_status(self, task_id: str, new_status: str, 
                          updated_by: str) -> Dict[str, Any]:
        """
        Обновить статус задачи
        
        Args:
            task_id: Идентификатор задачи
            new_status: Новый статус (CREATED, IN_PROGRESS, COMPLETED, CANCELLED)
            updated_by: Пользователь, обновивший статус
        
        Returns:
            Словарь с результатом операции
        """
        try:
            # Валидация входных данных
            if not task_id or not new_status or not updated_by:
                return format_response(
                    False,
                    error="Все параметры обязательны: task_id, new_status, updated_by"
                )
            
            task_id = sanitize_string(task_id)
            new_status = sanitize_string(new_status).upper()
            updated_by = sanitize_string(updated_by)
            
            # Валидация статуса
            if not validate_status(new_status):
                return format_response(
                    False,
                    error=f"Недопустимый статус: {new_status}. Допустимые значения: CREATED, IN_PROGRESS, COMPLETED, CANCELLED, CONFIRMED"
                )
            
            # Получаем задачу
            task_key = create_task_key(task_id)
            task = self.state.get_state(task_key)
            
            if not task:
                return format_response(
                    False,
                    error=f"Задача с ID {task_id} не найдена"
                )
            
            # Обновляем статус
            old_status = task.get("status")
            task["status"] = new_status
            task["updated_at"] = get_current_timestamp()
            task["updated_by"] = updated_by
            
            # Сохраняем обновленную задачу
            if self.state.put_state(task_key, task):
                logger.info(f"Статус задачи {task_id} обновлен с {old_status} на {new_status}")
                return format_response(True, data={
                    "task": task,
                    "old_status": old_status,
                    "new_status": new_status
                })
            else:
                return format_response(
                    False,
                    error="Не удалось обновить задачу в ledger"
                )
        
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса задачи: {str(e)}")
            return format_response(False, error=str(e))
    
    def add_document_version(self, task_id: str, document_id: str, 
                            version: str, content_hash: str, 
                            uploaded_by: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Добавить версию документа к задаче
        
        Args:
            task_id: Идентификатор задачи
            document_id: Идентификатор документа
            version: Версия документа (например, "1.0", "2.0")
            content_hash: Хеш содержимого документа
            uploaded_by: Пользователь, загрузивший документ
            metadata: Дополнительные метаданные документа
        
        Returns:
            Словарь с результатом операции
        """
        try:
            # Валидация входных данных
            version_data = {
                "version": version,
                "content_hash": content_hash,
                "uploaded_by": uploaded_by
            }
            
            is_valid, error_msg = validate_document_version_data(version_data)
            if not is_valid:
                return format_response(False, error=error_msg)
            
            # Очистка и нормализация данных
            task_id = sanitize_string(task_id)
            document_id = sanitize_string(document_id)
            version = sanitize_string(version)
            content_hash = sanitize_string(content_hash)
            uploaded_by = sanitize_string(uploaded_by)
            
            # Парсинг метаданных
            if isinstance(metadata, str):
                metadata = parse_metadata(metadata)
            elif metadata is None:
                metadata = {}
            
            # Получаем задачу
            task_key = create_task_key(task_id)
            task = self.state.get_state(task_key)
            
            if not task:
                return format_response(
                    False,
                    error=f"Задача с ID {task_id} не найдена"
                )
            
            # Создаем версию документа
            document_version = {
                "document_id": document_id,
                "version": version,
                "content_hash": content_hash,
                "uploaded_by": uploaded_by,
                "uploaded_at": get_current_timestamp(),
                "metadata": metadata
            }
            
            # Инициализируем список документов, если его нет
            if "documents" not in task:
                task["documents"] = []
            
            # Проверяем, существует ли уже документ с таким ID
            document_exists = False
            for doc in task["documents"]:
                if doc.get("document_id") == document_id:
                    # Добавляем версию к существующему документу
                    if "versions" not in doc:
                        doc["versions"] = []
                    doc["versions"].append(document_version)
                    document_exists = True
                    break
            
            # Если документа нет, создаем новый
            if not document_exists:
                task["documents"].append({
                    "document_id": document_id,
                    "created_at": get_current_timestamp(),
                    "versions": [document_version]
                })
            
            # Обновляем время изменения задачи
            task["updated_at"] = get_current_timestamp()
            
            # Сохраняем обновленную задачу
            if self.state.put_state(task_key, task):
                logger.info(f"Версия {version} документа {document_id} добавлена к задаче {task_id}")
                return format_response(True, data={
                    "task": task,
                    "document_version": document_version
                })
            else:
                return format_response(
                    False,
                    error="Не удалось обновить задачу в ledger"
                )
        
        except Exception as e:
            logger.error(f"Ошибка при добавлении версии документа: {str(e)}")
            return format_response(False, error=str(e))
    
    def get_document_versions(self, task_id: str, document_id: str) -> Dict[str, Any]:
        """
        Получить все версии документа
        
        Args:
            task_id: Идентификатор задачи
            document_id: Идентификатор документа
        
        Returns:
            Словарь с результатом операции и списком версий
        """
        try:
            # Валидация входных данных
            if not task_id or not document_id:
                return format_response(
                    False,
                    error="Оба параметра обязательны: task_id, document_id"
                )
            
            task_id = sanitize_string(task_id)
            document_id = sanitize_string(document_id)
            
            # Получаем задачу
            task_key = create_task_key(task_id)
            task = self.state.get_state(task_key)
            
            if not task:
                return format_response(
                    False,
                    error=f"Задача с ID {task_id} не найдена"
                )
            
            # Ищем документ
            document = None
            for doc in task.get("documents", []):
                if doc.get("document_id") == document_id:
                    document = doc
                    break
            
            if not document:
                return format_response(
                    False,
                    error=f"Документ с ID {document_id} не найден в задаче {task_id}"
                )
            
            # Возвращаем версии документа
            versions = document.get("versions", [])
            return format_response(True, data={
                "task_id": task_id,
                "document_id": document_id,
                "versions": versions,
                "total_versions": len(versions)
            })
        
        except Exception as e:
            logger.error(f"Ошибка при получении версий документа: {str(e)}")
            return format_response(False, error=str(e))
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Получить задачу по ID
        
        Args:
            task_id: Идентификатор задачи
        
        Returns:
            Словарь с результатом операции и данными задачи
        """
        try:
            if not task_id:
                return format_response(False, error="task_id обязателен")
            
            task_id = sanitize_string(task_id)
            task_key = create_task_key(task_id)
            task = self.state.get_state(task_key)
            
            if not task:
                return format_response(
                    False,
                    error=f"Задача с ID {task_id} не найдена"
                )
            
            return format_response(True, data={"task": task})
        
        except Exception as e:
            logger.error(f"Ошибка при получении задачи: {str(e)}")
            return format_response(False, error=str(e))


def invoke_chaincode(stub, function: str, args: List[str]) -> bytes:
    """
    Обработчик вызовов chaincode
    
    Args:
        stub: ChaincodeStubInterface
        function: Имя функции
        args: Аргументы функции
    
    Returns:
        Результат выполнения в виде bytes
    """
    import json
    
    chaincode = NPAChaincode(stub)
    
    try:
        if function == "createTask":
            if len(args) != 5:
                return json.dumps(format_response(
                    False,
                    error="Неверное количество аргументов. Ожидается: task_id, title, description, assignee, creator"
                )).encode('utf-8')
            
            result = chaincode.create_task(
                task_id=args[0],
                title=args[1],
                description=args[2],
                assignee=args[3],
                creator=args[4]
            )
        
        elif function == "updateTaskStatus":
            if len(args) != 3:
                return json.dumps(format_response(
                    False,
                    error="Неверное количество аргументов. Ожидается: task_id, new_status, updated_by"
                )).encode('utf-8')
            
            result = chaincode.update_task_status(
                task_id=args[0],
                new_status=args[1],
                updated_by=args[2]
            )
        
        elif function == "addDocumentVersion":
            if len(args) < 5:
                return json.dumps(format_response(
                    False,
                    error="Неверное количество аргументов. Ожидается: task_id, document_id, version, content_hash, uploaded_by, [metadata_json]"
                )).encode('utf-8')
            
            metadata = None
            if len(args) > 5:
                metadata = parse_metadata(args[5])
            
            result = chaincode.add_document_version(
                task_id=args[0],
                document_id=args[1],
                version=args[2],
                content_hash=args[3],
                uploaded_by=args[4],
                metadata=metadata
            )
        
        elif function == "getDocumentVersions":
            if len(args) != 2:
                return json.dumps(format_response(
                    False,
                    error="Неверное количество аргументов. Ожидается: task_id, document_id"
                )).encode('utf-8')
            
            result = chaincode.get_document_versions(
                task_id=args[0],
                document_id=args[1]
            )
        
        elif function == "getTask":
            if len(args) != 1:
                return json.dumps(format_response(
                    False,
                    error="Неверное количество аргументов. Ожидается: task_id"
                )).encode('utf-8')
            
            result = chaincode.get_task(task_id=args[0])
        
        else:
            result = format_response(
                False,
                error=f"Неизвестная функция: {function}"
            )
        
        return json.dumps(result).encode('utf-8')
    
    except Exception as e:
        logger.error(f"Ошибка при выполнении функции {function}: {str(e)}")
        return json.dumps(format_response(False, error=str(e))).encode('utf-8')

