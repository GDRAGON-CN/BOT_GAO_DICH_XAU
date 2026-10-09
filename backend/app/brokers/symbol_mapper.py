from typing import Dict
from app.core.config import settings

class SymbolMapper:
    """Translates generic symbols like XAUUSD to broker-specific symbols like XAUUSD+ or GOLD."""

    def __init__(self, mapping: Dict[str, str] = None):
        self._map = mapping or settings.BROKER_SYMBOL_MAP

    def to_broker(self, symbol: str) -> str:
        s = symbol.upper().strip()
        return self._map.get(s, s)

    def to_standard(self, broker_symbol: str) -> str:
        bs = broker_symbol.upper().strip()
        for std, brk in self._map.items():
            if brk.upper() == bs:
                return std
        return bs

symbol_mapper = SymbolMapper()
