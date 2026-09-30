from gateway_manager.cli.usage import run
from gateway_manager.usage import (
    SQLiteUsageRepository,
    UsageRecord,
)


def test_usage_cli_reports_usage(
    tmp_path,
    capsys,
):

    repository = SQLiteUsageRepository(
        tmp_path / "usage.db"
    )

    repository.add(
        UsageRecord.create(
            provider="openrouter",
            model="openrouter-gemma",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_amount=0.25,
            cost_currency="USD",
            success=True,
            fallback=False,
        )
    )

    repository.add(
        UsageRecord.create(
            provider="ollama",
            model="laguna-xs-2.1",
            prompt_tokens=20,
            completion_tokens=5,
            total_tokens=25,
            cost_amount=0.0,
            cost_currency="EUR",
            success=True,
            fallback=True,
        )
    )

    run(
        repository=repository
    )

    output = (
        capsys
        .readouterr()
        .out
    )

    assert "Gateway Usage" in output
    assert "requests" in output
    assert "fallbacks" in output
    assert "cost USD" in output
    assert "cost EUR" in output
