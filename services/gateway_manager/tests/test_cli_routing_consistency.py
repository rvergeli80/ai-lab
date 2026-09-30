from gateway_manager.cli.select import run
from gateway_manager.availability import (
    ProviderAvailability,
)


def test_cli_select_uses_available_providers(
    monkeypatch,
    capsys,
):

    monkeypatch.setattr(
        ProviderAvailability,
        "available",
        lambda self: {
            "ollama",
        },
    )

    run(
        capability="chat",
        tag=None,
    )

    output = (
        capsys
        .readouterr()
        .out
        .strip()
    )

    assert (
        output
        == "laguna-xs-2.1"
    )
