#!/usr/bin/env python3
"""
Тестовый скрипт для проверки REST API chaincode
"""

import requests
import json

BASE_URL = "http://localhost:8080/api/v1"


def test_create_task():
    """Тест создания задачи"""
    print("\n=== Тест создания задачи ===")
    
    data = {
        "task_id": "TASK001",
        "title": "Тестовая задача",
        "description": "Описание тестовой задачи",
        "assignee": "user1",
        "creator": "admin"
    }
    
    response = requests.post(f"{BASE_URL}/tasks", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_get_task(task_id):
    """Тест получения задачи"""
    print(f"\n=== Тест получения задачи {task_id} ===")
    
    response = requests.get(f"{BASE_URL}/tasks/{task_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_update_task_status(task_id):
    """Тест обновления статуса задачи"""
    print(f"\n=== Тест обновления статуса задачи {task_id} ===")
    
    data = {
        "status": "IN_PROGRESS",
        "updated_by": "user1"
    }
    
    response = requests.put(f"{BASE_URL}/tasks/{task_id}/status", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_add_document_version(task_id, document_id):
    """Тест добавления версии документа"""
    print(f"\n=== Тест добавления версии документа ===")
    
    data = {
        "version": "1.0",
        "content_hash": "abc123def456",
        "uploaded_by": "user1",
        "metadata": {
            "filename": "test_document.pdf",
            "size": 1024,
            "mime_type": "application/pdf"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/tasks/{task_id}/documents/{document_id}/versions",
        json=data
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_get_document_versions(task_id, document_id):
    """Тест получения версий документа"""
    print(f"\n=== Тест получения версий документа ===")
    
    response = requests.get(
        f"{BASE_URL}/tasks/{task_id}/documents/{document_id}/versions"
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def main():
    """Запуск всех тестов"""
    print("="*60)
    print("Тестирование REST API Chaincode")
    print("="*60)
    
    try:
        # Проверка здоровья сервиса
        response = requests.get("http://localhost:8080/health")
        print(f"\nHealth check: {response.status_code}")
        if response.status_code != 200:
            print("❌ Сервис недоступен. Убедитесь, что REST API запущен.")
            return
        
        # Создание задачи
        task_result = test_create_task()
        if not task_result.get("success"):
            print("❌ Не удалось создать задачу")
            return
        
        task_id = "TASK001"
        
        # Получение задачи
        test_get_task(task_id)
        
        # Обновление статуса
        test_update_task_status(task_id)
        
        # Добавление версии документа
        document_id = "DOC001"
        test_add_document_version(task_id, document_id)
        
        # Добавление еще одной версии
        data = {
            "version": "2.0",
            "content_hash": "xyz789ghi012",
            "uploaded_by": "user2",
            "metadata": {
                "filename": "test_document_v2.pdf",
                "size": 2048
            }
        }
        requests.post(
            f"{BASE_URL}/tasks/{task_id}/documents/{document_id}/versions",
            json=data
        )
        
        # Получение версий документа
        test_get_document_versions(task_id, document_id)
        
        print("\n" + "="*60)
        print("✓ Все тесты выполнены")
        print("="*60)
    
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к сервису")
        print("   Убедитесь, что REST API запущен: python src/rest_api.py")
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")


if __name__ == "__main__":
    main()

