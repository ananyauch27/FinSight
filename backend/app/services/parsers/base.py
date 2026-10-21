from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from abc import ABC, abstractmethod

@dataclass

class ParsedTxn:
    txn_date : date
    description : str
    amount : Decimal
    direction : str
    balance : Decimal | None = None
    reference : str | None = None 


class BaseParser(ABC):
    bank_code : str = "generic"

    @abstractmethod
    def can_parse(self, sample_text : str, filename : str) -> bool:
        """Cheap check using header text or filename."""

    @abstractmethod
    def parse(self, path: str, password: str | None = None) -> list[ParsedTxn]:
        ...