from gateway_manager.catalog import CatalogLoader


def test_catalog_loader_loads_models():

    catalog = CatalogLoader.load()

    assert "gpt-5" in catalog["models"]
    assert "gpt-5-mini" in catalog["models"]
    assert "openrouter-gemma" in catalog["models"]