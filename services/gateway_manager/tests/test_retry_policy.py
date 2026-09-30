import httpx

from gateway_manager.routing import (
    RetryPolicy,
)


def test_retry_policy_classifies_rate_limit():

    policy = RetryPolicy()

    exc = Exception(
        "rate limit exceeded"
    )

    assert (
        policy.classify(exc)
        == "rate_limit"
    )

    assert (
        policy.allows_retry(exc)
        is True
    )


def test_retry_policy_classifies_quota():

    policy = RetryPolicy()

    exc = RuntimeError(
        "insufficient credits"
    )

    assert (
        policy.classify(exc)
        == "quota_exceeded"
    )

    assert (
        policy.allows_retry(exc)
        is True
    )


def test_retry_policy_classifies_timeout():

    policy = RetryPolicy()

    exc = httpx.ReadTimeout(
        "timed out"
    )

    assert (
        policy.classify(exc)
        == "timeout"
    )

    assert (
        policy.allows_retry(exc)
        is True
    )


def test_retry_policy_rejects_unknown_error():

    policy = RetryPolicy()

    exc = ValueError(
        "invalid application input"
    )

    assert (
        policy.classify(exc)
        is None
    )

    assert (
        policy.allows_retry(exc)
        is False
    )
