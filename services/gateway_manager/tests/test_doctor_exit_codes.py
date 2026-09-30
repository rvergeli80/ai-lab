from gateway_manager.availability import (
    ProviderAvailability,
)
from gateway_manager.doctor import (
    GatewayDoctor,
)


def test_doctor_returns_zero_when_healthy(
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

    exit_code = (
        GatewayDoctor.run()
    )

    capsys.readouterr()

    assert exit_code == 0


def test_doctor_returns_one_when_degraded(
    monkeypatch,
    capsys,
):

    monkeypatch.setattr(
        ProviderAvailability,
        "available",
        lambda self: set(),
    )

    exit_code = (
        GatewayDoctor.run()
    )

    capsys.readouterr()

    assert exit_code == 1
