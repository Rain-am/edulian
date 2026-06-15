from __future__ import annotations

from abc import ABC, abstractmethod

from src.shipment.models import RawCustomsData


class CustomsDataSource(ABC):
    @abstractmethod
    def load(self, shipment_time: str | None = None) -> RawCustomsData:
        raise NotImplementedError
