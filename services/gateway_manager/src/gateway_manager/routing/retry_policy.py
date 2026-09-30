import httpx

from .policy_loader import PolicyLoader


class RetryPolicy:

    def __init__(
        self,
        config: dict | None = None,
    ) -> None:

        self.config = (
            config
            or PolicyLoader.load()
        )

        self.retryable_errors = set(
            self.config
            .get("fallback", {})
            .get(
                "retryable_errors",
                [],
            )
        )

    def allows_retry(
        self,
        exc: Exception,
    ) -> bool:

        category = self.classify(
            exc
        )

        if category is None:
            return False

        return (
            category
            in self.retryable_errors
        )

    def classify(
        self,
        exc: Exception,
    ) -> str | None:

        if isinstance(
            exc,
            httpx.TimeoutException,
        ):
            return "timeout"

        if isinstance(
            exc,
            httpx.ConnectError,
        ):
            return "provider_unavailable"

        if isinstance(
            exc,
            httpx.HTTPStatusError,
        ):
            return self._from_status(
                exc.response.status_code
            )

        status = getattr(
            exc,
            "status_code",
            None,
        )

        if isinstance(
            status,
            int,
        ):
            category = (
                self._from_status(
                    status
                )
            )

            if category is not None:
                return category

        message = str(
            exc
        ).lower()

        markers = (
            (
                "rate limit",
                "rate_limit",
            ),
            (
                "too many requests",
                "rate_limit",
            ),
            (
                "quota",
                "quota_exceeded",
            ),
            (
                "insufficient credits",
                "quota_exceeded",
            ),
            (
                "insufficient credit",
                "quota_exceeded",
            ),
            (
                "timeout",
                "timeout",
            ),
            (
                "timed out",
                "timeout",
            ),
            (
                "service unavailable",
                "provider_unavailable",
            ),
            (
                "provider unavailable",
                "provider_unavailable",
            ),
            (
                "connection error",
                "provider_unavailable",
            ),
            (
                "connection refused",
                "provider_unavailable",
            ),
            (
                "model unavailable",
                "model_unavailable",
            ),
            (
                "model not found",
                "model_unavailable",
            ),
        )

        for marker, category in markers:

            if marker in message:
                return category

        return None

    @staticmethod
    def _from_status(
        status: int,
    ) -> str | None:

        if status == 429:
            return "rate_limit"

        if status == 402:
            return "quota_exceeded"

        if status in {
            408,
            504,
        }:
            return "timeout"

        if status == 404:
            return "model_unavailable"

        if (
            status in {
                401,
                403,
                409,
                425,
            }
            or status >= 500
        ):
            return "provider_unavailable"

        return None
