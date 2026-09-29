from abc import ABC, abstractmethod
from datetime import datetime

from .usage_record import UsageRecord


class UsageRepository(ABC):

    @abstractmethod
    def add(self, record: UsageRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_between(
        self,
        start: datetime,
        end: datetime,
    ) -> list[UsageRecord]:
        raise NotImplementedError

    @abstractmethod
    def total_cost_between(
        self,
        start: datetime,
        end: datetime,
    ) -> float:
        raise NotImplementedError
