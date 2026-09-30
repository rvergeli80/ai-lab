from gateway_manager.validation import (
    GatewayConfigValidator,
)


def test_current_gateway_configuration_is_valid():

    result = (
        GatewayConfigValidator
        .validate()
    )

    assert result.valid is True
    assert result.errors == ()


def test_validator_exposes_warnings_separately():

    result = (
        GatewayConfigValidator
        .validate()
    )

    assert isinstance(
        result.warnings,
        tuple,
    )
