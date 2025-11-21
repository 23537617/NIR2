"""
NPA Chaincode Package
Chaincode для управления задачами и версиями документов
"""

__version__ = "1.0.0"

from .chaincode import NPAChaincode
from .state import StateManager
from .utils import validate_status, format_response

__all__ = [
    "NPAChaincode",
    "StateManager",
    "validate_status",
    "format_response"
]

