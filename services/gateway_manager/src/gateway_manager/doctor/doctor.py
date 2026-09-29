import os

from gateway_manager.catalog import CatalogLoader
from gateway_manager.providers import PROVIDERS


class GatewayDoctor:

    @classmethod
    def run(cls):

        catalog = CatalogLoader.load()

        print()
        print("Gateway Doctor")
        print("=" * 60)

        print("\nProviders")

        for name, provider in PROVIDERS.items():

            status = "OK" if os.getenv(provider.env) else "MISSING"

            print(f"{name:<15} {status}")

        print("\nModels")

        for model in sorted(catalog["models"]):
            print(f"- {model}")

        print("\nAliases")

        for alias, target in catalog["aliases"].items():
            print(f"{alias:<20} -> {target}")

        print()