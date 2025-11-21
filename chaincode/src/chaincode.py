#!/usr/bin/env python3
"""
Основной chaincode для управления задачами и документами
Реализует функции: createTask, updateTaskStatus, addDocumentVersion, getDocumentVersions
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TaskDocumentChaincode:
    """Chaincode для управления задачами и версиями документов"""
    
    def __init__(self, stub):
        """
        Инициализация chaincode
        
        Args:
            stub: ChaincodeStubInterface для взаимодействия с ledger
        """
        self.stub = stub
    
    def _get_state(self, key: str) -> Optional[Dict[str, Any]]:
        """Получить значение из ledger"""
        try:
            state = self.stub.get_state(key)
            if not state or len(state) == 0:
                return None
            return json.loads(state.decode('utf-8'))
        except Exception as e:
            logger.error(f"Ошибка при получении состояния для ключа {key}: {str(e)}")
            return None
    
    def _put_state(self, key: str, value: Dict[str, Any]) -> bool:
        """Сохранить значение в ledger"""
        try:
            self.stub.put_state(key, json.dumps(value).encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении состояния для ключа {key}: {str(e)}")
            return False
    
    def _get_composite_key(self, object_type: str, attributes: List[str]) -> str:
        """Создать составной ключ"""
        return self.stub.create_composite_key(object_type, attributes)
    
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
            # Проверяем, не существует ли уже задача с таким ID
            task_key = f"TASK_{task_id}"
            existing_task = self._get_state(task_key)
            if existing_task:
                return {
                    "success": False,
                    "error": f"Задача с ID {task_id} уже существует"
                }
            
            # Создаем новую задачу
            task = {
                "task_id": task_id,
                "title": title,
                "description": description,
                "assignee": assignee,
                "creator": creator,
                "status": "CREATED",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "documents": []
            }
            
            # Сохраняем задачу
            if self._put_state(task_key, task):
                logger.info(f"Задача {task_id} успешно создана")
                return {
                    "success": True,
                    "task": task
                }
            else:
                return {
                    "success": False,
                    "error": "Не удалось сохранить задачу в ledger"
                }
        
        except Exception as e:
            logger.error(f"Ошибка при создании задачи: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
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
            # Получаем задачу
            task_key = f"TASK_{task_id}"
            task = self._get_state(task_key)
            
            if not task:
                return {
                    "success": False,
                    "error": f"Задача с ID {task_id} не найдена"
                }
            
            # Валидация статуса
            valid_statuses = ["CREATED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]
            if new_status not in valid_statuses:
                return {
                    "success": False,
                    "error": f"Недопустимый статус. Допустимые значения: {', '.join(valid_statuses)}"
                }
            
            # Обновляем статус
            old_status = task.get("status")
            task["status"] = new_status
            task["updated_at"] = datetime.utcnow().isoformat()
            task["updated_by"] = updated_by
            
            # Сохраняем обновленную задачу
            if self._put_state(task_key, task):
                logger.info(f"Статус задачи {task_id} обновлен с {old_status} на {new_status}")
                return {
                    "success": True,
                    "task": task,
                    "old_status": old_status,
                    "new_status": new_status
                }
            else:
                return {
                    "success": False,
                    "error": "Не удалось обновить задачу в ledger"
                }
        
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса задачи: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
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
            # Получаем задачу
            task_key = f"TASK_{task_id}"
            task = self._get_state(task_key)
            
            if not task:
                return {
                    "success": False,
                    "error": f"Задача с ID {task_id} не найдена"
                }
            
            # Создаем версию документа
            document_version = {
                "document_id": document_id,
                "version": version,
                "content_hash": content_hash,
                "uploaded_by": uploaded_by,
                "uploaded_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
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
                    "created_at": datetime.utcnow().isoformat(),
                    "versions": [document_version]
                })
            
            # Обновляем время изменения задачи
            task["updated_at"] = datetime.utcnow().isoformat()
            
            # Сохраняем обновленную задачу
            if self._put_state(task_key, task):
                logger.info(f"Версия {version} документа {document_id} добавлена к задаче {task_id}")
                return {
                    "success": True,
                    "task": task,
                    "document_version": document_version
                }
            else:
                return {
                    "success": False,
                    "error": "Не удалось обновить задачу в ledger"
                }
        
        except Exception as e:
            logger.error(f"Ошибка при добавлении версии документа: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
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
            # Получаем задачу
            task_key = f"TASK_{task_id}"
            task = self._get_state(task_key)
            
            if not task:
                return {
                    "success": False,
                    "error": f"Задача с ID {task_id} не найдена"
                }
            
            # Ищем документ
            document = None
            for doc in task.get("documents", []):
                if doc.get("document_id") == document_id:
                    document = doc
                    break
            
            if not document:
                return {
                    "success": False,
                    "error": f"Документ с ID {document_id} не найден в задаче {task_id}"
                }
            
            # Возвращаем версии документа
            versions = document.get("versions", [])
            return {
                "success": True,
                "task_id": task_id,
                "document_id": document_id,
                "versions": versions,
                "total_versions": len(versions)
            }
        
        except Exception as e:
            logger.error(f"Ошибка при получении версий документа: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Получить задачу по ID
        
        Args:
            task_id: Идентификатор задачи
        
        Returns:
            Словарь с результатом операции и данными задачи
        """
        try:
            task_key = f"TASK_{task_id}"
            task = self._get_state(task_key)
            
            if not task:
                return {
                    "success": False,
                    "error": f"Задача с ID {task_id} не найдена"
                }
            
            return {
                "success": True,
                "task": task
            }
        
        except Exception as e:
            logger.error(f"Ошибка при получении задачи: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


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
    chaincode = TaskDocumentChaincode(stub)
    
    try:
        if function == "createTask":
            if len(args) != 5:
                return json.dumps({
                    "success": False,
                    "error": "Неверное количество аргументов. Ожидается: task_id, title, description, assignee, creator"
                }).encode('utf-8')
            
            result = chaincode.create_task(
                task_id=args[0],
                title=args[1],
                description=args[2],
                assignee=args[3],
                creator=args[4]
            )
        
        elif function == "updateTaskStatus":
            if len(args) != 3:
                return json.dumps({
                    "success": False,
                    "error": "Неверное количество аргументов. Ожидается: task_id, new_status, updated_by"
                }).encode('utf-8')
            
            result = chaincode.update_task_status(
                task_id=args[0],
                new_status=args[1],
                updated_by=args[2]
            )
        
        elif function == "addDocumentVersion":
            if len(args) < 5:
                return json.dumps({
                    "success": False,
                    "error": "Неверное количество аргументов. Ожидается: task_id, document_id, version, content_hash, uploaded_by, [metadata_json]"
                }).encode('utf-8')
            
            metadata = None
            if len(args) > 5:
                try:
                    metadata = json.loads(args[5])
                except:
                    metadata = {}
            
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
                return json.dumps({
                    "success": False,
                    "error": "Неверное количество аргументов. Ожидается: task_id, document_id"
                }).encode('utf-8')
            
            result = chaincode.get_document_versions(
                task_id=args[0],
                document_id=args[1]
            )
        
        elif function == "getTask":
            if len(args) != 1:
                return json.dumps({
                    "success": False,
                    "error": "Неверное количество аргументов. Ожидается: task_id"
                }).encode('utf-8')
            
            result = chaincode.get_task(task_id=args[0])
        
        else:
            result = {
                "success": False,
                "error": f"Неизвестная функция: {function}"
            }
        
        return json.dumps(result).encode('utf-8')
    
    except Exception as e:
        logger.error(f"Ошибка при выполнении функции {function}: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }).encode('utf-8')

