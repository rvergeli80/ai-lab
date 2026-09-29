import os

import httpx

from gateway_manager.providers import PROVIDERS


class ProviderAvailability:

    def available(self) -> set[str]:

        available = set()

        for provider in PROVIDERS.values():

            if provider.name == "ollama":

                host = os.getenv(
                    "OLLAMA_HOST",
                    "http://localhost:11434",
                ).rstrip("/")

                try:
                    response = httpx.get(
                        f"{host}/api/version",
                        timeout=2,
                    )

                    if response.is_success:
                        available.add("ollama")

                except httpx.HTTPError:
                    pass

                continue

            if os.getenv(provider.env):
                available.add(provider.name)

        return available
