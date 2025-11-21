#!/usr/bin/env python3
"""
REST API сервер для chaincode
Предоставляет HTTP интерфейс для вызова функций chaincode
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import sys

# Добавляем путь к модулю chaincode
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chaincode import TaskDocumentChaincode

# Упрощенная заглушка для REST API
class ChaincodeStub:
    """Заглушка для ChaincodeStubInterface для REST API"""
    
    def __init__(self):
        self.channel_id = ""
        self.tx_id = ""
        self.state = {}
    
    def get_state(self, key: str) -> bytes:
        """Получить состояние"""
        value = self.state.get(key)
        if value:
            return value.encode('utf-8') if isinstance(value, str) else value
        return b''
    
    def put_state(self, key: str, value: bytes) -> None:
        """Сохранить состояние"""
        self.state[key] = value.decode('utf-8') if isinstance(value, bytes) else value
    
    def create_composite_key(self, object_type: str, attributes: list) -> str:
        """Создать составной ключ"""
        return f"{object_type}:{':'.join(attributes)}"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для всех доменов


class RESTChaincodeStub(ChaincodeStub):
    """Заглушка для REST API (в production нужно подключение к реальному peer)"""
    
    def __init__(self):
        super().__init__("", "")
        self.state = {}
    
    def get_state(self, key: str) -> bytes:
        """Получить состояние"""
        value = self.state.get(key)
        if value:
            return value.encode('utf-8') if isinstance(value, str) else value
        return b''
    
    def put_state(self, key: str, value: bytes) -> None:
        """Сохранить состояние"""
        self.state[key] = value.decode('utf-8') if isinstance(value, bytes) else value


# Глобальный экземпляр chaincode
stub = ChaincodeStub()
chaincode = TaskDocumentChaincode(stub)


@app.route('/health', methods=['GET'])
def health():
    """Проверка здоровья сервиса"""
    return jsonify({
        "status": "healthy",
        "service": "TaskDocument Chaincode REST API"
    })


@app.route('/api/v1/tasks', methods=['POST'])
def create_task():
    """Создать новую задачу"""
    try:
        data = request.get_json()
        
        required_fields = ['task_id', 'title', 'description', 'assignee', 'creator']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Отсутствует обязательное поле: {field}"
                }), 400
        
        result = chaincode.create_task(
            task_id=data['task_id'],
            title=data['title'],
            description=data['description'],
            assignee=data['assignee'],
            creator=data['creator']
        )
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Ошибка при создании задачи: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/v1/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """Получить задачу по ID"""
    try:
        result = chaincode.get_task(task_id=task_id)
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Ошибка при получении задачи: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/v1/tasks/<task_id>/status', methods=['PUT'])
def update_task_status(task_id):
    """Обновить статус задачи"""
    try:
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify({
                "success": False,
                "error": "Отсутствует поле: status"
            }), 400
        
        if 'updated_by' not in data:
            return jsonify({
                "success": False,
                "error": "Отсутствует поле: updated_by"
            }), 400
        
        result = chaincode.update_task_status(
            task_id=task_id,
            new_status=data['status'],
            updated_by=data['updated_by']
        )
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса задачи: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/v1/tasks/<task_id>/documents/<document_id>/versions', methods=['POST'])
def add_document_version(task_id, document_id):
    """Добавить версию документа"""
    try:
        data = request.get_json()
        
        required_fields = ['version', 'content_hash', 'uploaded_by']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Отсутствует обязательное поле: {field}"
                }), 400
        
        result = chaincode.add_document_version(
            task_id=task_id,
            document_id=document_id,
            version=data['version'],
            content_hash=data['content_hash'],
            uploaded_by=data['uploaded_by'],
            metadata=data.get('metadata')
        )
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Ошибка при добавлении версии документа: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/v1/tasks/<task_id>/documents/<document_id>/versions', methods=['GET'])
def get_document_versions(task_id, document_id):
    """Получить все версии документа"""
    try:
        result = chaincode.get_document_versions(
            task_id=task_id,
            document_id=document_id
        )
        
        status_code = 200 if result.get('success') else 404
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Ошибка при получении версий документа: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Обработчик 404"""
    return jsonify({
        "success": False,
        "error": "Endpoint не найден"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Обработчик 500"""
    return jsonify({
        "success": False,
        "error": "Внутренняя ошибка сервера"
    }), 500


def main():
    """Запуск REST API сервера"""
    port = int(os.getenv('REST_API_PORT', '8080'))
    host = os.getenv('REST_API_HOST', '0.0.0.0')
    
    logger.info(f"Запуск REST API сервера на {host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    main()

