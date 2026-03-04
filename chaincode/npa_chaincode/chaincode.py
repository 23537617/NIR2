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
import json
from typing import Optional, Dict, Any, List

from fabric_chaincode_python.contract.contract_base import Contract
from fabric_chaincode_python.contract.metadata import metadata

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


@metadata(
    name="TaskDocument",
    version="1.0",
    info={
        "title": "Task and Document Management Chaincode",
        "description": "Chaincode for managing tasks and document versioning",
        "contact": {
            "name": "Antigravity",
            "email": "antigravity@example.com"
        }
    }
)
class NPAChaincode(Contract):
    """
    Основной класс NPA Chaincode для управления задачами и версиями документов
    
    Наследуется от Contract для использования официального SDK.
    """
    
    def __init__(self):
        """Инициализация Contract"""
        super().__init__()
        logger.info("NPA Chaincode инициализирован")

    def create_task(self, ctx, task_id: str, title: str, description: str, 
                   assignee: str, creator: str) -> str:
        """
        Создать новую задачу
        
        Args:
            ctx: Контекст транзакции
            task_id: Уникальный идентификатор задачи
            title: Название задачи
            description: Описание задачи
            assignee: Исполнитель задачи
            creator: Создатель задачи
        
        Returns:
            JSON строка с результатом операции
        """
        try:
            state = StateManager(ctx.stub)
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
                return json.dumps(format_response(False, error=error_msg))
            
            # Очистка строковых значений
            task_id = sanitize_string(task_id)
            title = sanitize_string(title)
            description = sanitize_string(description)
            assignee = sanitize_string(assignee)
            creator = sanitize_string(creator)
            
            # Проверяем, не существует ли уже задача с таким ID
            task_key = create_task_key(task_id)
            existing_task = state.get_state(task_key)
            
            if existing_task:
                return json.dumps(format_response(
                    False,
                    error=f"Задача с ID {task_id} уже существует"
                ))
            
            # Получаем личность вызывающего
            client_id = ctx.client_identity.get_id()
            msp_id = ctx.client_identity.get_msp_id()
            creator_identity = f"{msp_id}::{client_id}"
            
            # Создаем новую задачу
            task = {
                "task_id": task_id,
                "title": title,
                "description": description,
                "assignee": assignee,
                "creator": creator,
                "creator_identity": creator_identity,
                "status": TASK_STATUS_CREATED,
                "created_at": get_current_timestamp(),
                "updated_at": get_current_timestamp(),
                "documents": []
            }
            
            # Сохраняем задачу
            if state.put_state(task_key, task):
                # Генерируем событие
                ctx.stub.set_event("onTaskCreated", json.dumps({"task_id": task_id, "creator": creator}).encode('utf-8'))
                
                logger.info(f"Задача {task_id} успешно создана")
                return json.dumps(format_response(True, data={"task": task}))
            else:
                return json.dumps(format_response(
                    False,
                    error="Не удалось сохранить задачу в ledger"
                ))
        
        except Exception as e:
            logger.error(f"Ошибка при создании задачи: {str(e)}")
            return json.dumps(format_response(False, error=str(e)))
    
    def update_task_status(self, ctx, task_id: str, new_status: str, 
                          updated_by: str) -> str:
        """
        Обновить статус задачи
        
        Args:
            ctx: Контекст транзакции
            task_id: Идентификатор задачи
            new_status: Новый статус
            updated_by: Пользователь
        
        Returns:
            JSON строка с результатом операции
        """
        try:
            state = StateManager(ctx.stub)
            # Валидация входных данных
            if not task_id or not new_status or not updated_by:
                return json.dumps(format_response(
                    False,
                    error="Все параметры обязательны: task_id, new_status, updated_by"
                ))
            
            task_id = sanitize_string(task_id)
            new_status = sanitize_string(new_status).upper()
            updated_by = sanitize_string(updated_by)
            
            # Валидация статуса
            if not validate_status(new_status):
                return json.dumps(format_response(
                    False,
                    error=f"Недопустимый статус: {new_status}. Допустимые значения: CREATED, IN_PROGRESS, COMPLETED, CANCELLED, CONFIRMED"
                ))
            
            # Получаем задачу
            task_key = create_task_key(task_id)
            task = state.get_state(task_key)
            
            if not task:
                return json.dumps(format_response(
                    False,
                    error=f"Задача с ID {task_id} не найдена"
                ))
            
            # Обновляем статус
            old_status = task.get("status")
            task["status"] = new_status
            task["updated_at"] = get_current_timestamp()
            task["updated_by"] = updated_by
            task["last_updated_by_msp"] = ctx.client_identity.get_msp_id()
            task["last_updated_by_id"] = ctx.client_identity.get_id()
            
            # Сохраняем обновленную задачу
            if state.put_state(task_key, task):
                # Генерируем событие
                event_payload = {
                    "task_id": task_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "updated_by": updated_by
                }
                ctx.stub.set_event("onTaskStatusUpdated", json.dumps(event_payload).encode('utf-8'))
                
                logger.info(f"Статус задачи {task_id} обновлен с {old_status} на {new_status}")
                return json.dumps(format_response(True, data={
                    "task": task,
                    "old_status": old_status,
                    "new_status": new_status
                }))
            else:
                return json.dumps(format_response(
                    False,
                    error="Не удалось обновить задачу в ledger"
                ))
        
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса задачи: {str(e)}")
            return json.dumps(format_response(False, error=str(e)))
    
    def add_document_version(self, ctx, task_id: str, document_id: str, 
                            version: str, content_hash: str, 
                            uploaded_by: str, metadata_json: Optional[str] = None) -> str:
        """
        Добавить версию документа к задаче
        """
        try:
            state = StateManager(ctx.stub)
            # Валидация входных данных
            version_data = {
                "version": version,
                "content_hash": content_hash,
                "uploaded_by": uploaded_by
            }
            
            is_valid, error_msg = validate_document_version_data(version_data)
            if not is_valid:
                return json.dumps(format_response(False, error=error_msg))
            
            # Очистка и нормализация данных
            task_id = sanitize_string(task_id)
            document_id = sanitize_string(document_id)
            version = sanitize_string(version)
            content_hash = sanitize_string(content_hash)
            uploaded_by = sanitize_string(uploaded_by)
            
            # Парсинг метаданных
            metadata = parse_metadata(metadata_json)
            
            # Получаем задачу
            task_key = create_task_key(task_id)
            task = state.get_state(task_key)
            
            if not task:
                return json.dumps(format_response(
                    False,
                    error=f"Задача с ID {task_id} не найдена"
                ))
            
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
            if state.put_state(task_key, task):
                logger.info(f"Версия {version} документа {document_id} добавлена к задаче {task_id}")
                return json.dumps(format_response(True, data={
                    "task": task,
                    "document_version": document_version
                }))
            else:
                return json.dumps(format_response(
                    False,
                    error="Не удалось обновить задачу в ledger"
                ))
        
        except Exception as e:
            logger.error(f"Ошибка при добавлении версии документа: {str(e)}")
            return json.dumps(format_response(False, error=str(e)))

    def get_document_versions(self, ctx, task_id: str, document_id: str) -> str:
        """
        Получить все версии документа
        """
        try:
            state = StateManager(ctx.stub)
            # Валидация входных данных
            if not task_id or not document_id:
                return json.dumps(format_response(
                    False,
                    error="Оба параметра обязательны: task_id, document_id"
                ))
            
            task_id = sanitize_string(task_id)
            document_id = sanitize_string(document_id)
            
            # Получаем задачу
            task_key = create_task_key(task_id)
            task = state.get_state(task_key)
            
            if not task:
                return json.dumps(format_response(
                    False,
                    error=f"Задача с ID {task_id} не найдена"
                ))
            
            # Ищем документ
            document: Optional[Dict[str, Any]] = None
            raw_docs = task.get("documents", [])
            documents: List[Dict[str, Any]] = raw_docs if isinstance(raw_docs, list) else []
            
            for doc in documents:
                if not isinstance(doc, dict):
                    continue
                if doc.get("document_id") == document_id:
                    document = doc
                    break
            
            if document is None or not isinstance(document, dict):
                return json.dumps(format_response(
                    False,
                    error=f"Документ с ID {document_id} не найден в задаче {task_id}"
                ))
            
            # Возвращаем версии документа
            versions = document.get("versions", [])
            return json.dumps(format_response(True, data={
                "task_id": task_id,
                "document_id": document_id,
                "versions": versions,
                "total_versions": len(versions)
            }))
        
        except Exception as e:
            logger.error(f"Ошибка при получении версий документа: {str(e)}")
            return json.dumps(format_response(False, error=str(e)))
    
    def get_task(self, ctx, task_id: str) -> str:
        """
        Получить задачу по ID
        """
        try:
            state = StateManager(ctx.stub)
            if not task_id:
                return json.dumps(format_response(False, error="task_id обязателен"))
            
            task_id = sanitize_string(task_id)
            task_key = create_task_key(task_id)
            task = state.get_state(task_key)
            
            if not task:
                return json.dumps(format_response(
                    False,
                    error=f"Задача с ID {task_id} не найдена"
                ))
            
            return json.dumps(format_response(True, data={"task": task}))
        
        except Exception as e:
            logger.error(f"Ошибка при получении задачи: {str(e)}")
            return json.dumps(format_response(False, error=str(e)))
    
    def get_task_history(self, ctx, task_id: str) -> str:
        """
        Получить историю изменений задачи
        """
        try:
            state = StateManager(ctx.stub)
            task_key = create_task_key(sanitize_string(task_id))
            history = state.get_history_for_key(task_key)
            
            return json.dumps(format_response(True, data={
                "task_id": task_id,
                "history": history,
                "total_entries": len(history)
            }))
        except Exception as e:
            logger.error(f"Ошибка при получении истории задачи {task_id}: {str(e)}")
            return json.dumps(format_response(False, error=str(e)))

    def query_tasks(self, ctx, query_json: str, page_size: Optional[str] = None, 
                   bookmark: Optional[str] = None) -> str:
        """
        Выполнить произвольный запрос к задачам (CouchDB selector)
        Поддерживает пагинацию если указаны page_size и bookmark.
        """
        try:
            state = StateManager(ctx.stub)
            
            if page_size:
                results_data = state.get_query_result_with_pagination(
                    query_json, int(page_size), bookmark or ""
                )
                return json.dumps(format_response(True, data=results_data))
            else:
                results = state.get_query_result(query_json)
                return json.dumps(format_response(True, data={
                    "results": results,
                    "total_results": len(results)
                }))
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса: {str(e)}")
            return json.dumps(format_response(False, error=str(e)))

