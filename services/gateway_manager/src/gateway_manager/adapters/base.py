from abc import ABC, abstractmethod

from gateway_manager.adapters.dto import ProviderResponse
from gateway_manager.domain import Request


class LLMAdapter(ABC):

    @abstractmethod
    def complete(
        self,
        model_name: str,
        request: Request,
    ) -> ProviderResponse:
        ...