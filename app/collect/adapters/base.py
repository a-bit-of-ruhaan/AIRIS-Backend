from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel
from datetime import datetime

class ParserResult(BaseModel):
    is_valid: bool
    quotes: List[Dict[str, Any]]
    error: Optional[str] = None
    expected_yield: tuple[int, int]
    parser_version: str

class SourceAdapter(ABC):
    source_id: str
    source_name: str
    is_direct: bool
    parser_version: str
    
    @abstractmethod
    def check_policy(self) -> bool:
        """Check robots.txt or other policy before collection."""
        pass
        
    @abstractmethod
    def collect(self, query: Dict[str, Any]) -> tuple[Dict[str, Any], Optional[str]]:
        """
        Execute collection for a single query.
        Returns (raw_payload, error_message).
        """
        pass
        
    @abstractmethod
    def parse(self, raw_payload: Dict[str, Any], query: Dict[str, Any]) -> ParserResult:
        """
        Parse raw payload into structured quote dictionaries.
        """
        pass
