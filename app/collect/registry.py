from typing import Dict, Type
from app.collect.adapters.base import SourceAdapter

class ParserRegistry:
    def __init__(self):
        self._adapters: Dict[str, SourceAdapter] = {}
        
    def register(self, adapter: SourceAdapter):
        self._adapters[adapter.source_id] = adapter
        
    def get_adapter(self, source_id: str) -> SourceAdapter:
        if source_id not in self._adapters:
            raise ValueError(f"No adapter registered for source: {source_id}")
        return self._adapters[source_id]
        
    def list_adapters(self) -> list[SourceAdapter]:
        return list(self._adapters.values())

registry = ParserRegistry()
