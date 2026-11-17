from __future__ import annotations

import json
import logging

import pytest

from app_base.core.settings import Settings
from app_base.core.telemetry import OTelLogHandler

pytestmark = pytest.mark.unit


def test_diddigo_onboarding_variable_contract_is_supported() -> None:
    configured = Settings(
        ENVIRONMENT="staging",
        DEPLOYMENT_ID="diddigo-staging",
        METRICS_BEARER_TOKEN="synthetic-metrics-token",
        OTEL_EXPORTER_OTLP_ENDPOINT="http://collector/otlp/diddigo",
        OTEL_EXPORTER_OTLP_LOGS_ENDPOINT="http://collector/otlp/diddigo/v1/logs",
        OTEL_LOGS_ENABLED=True,
    )

    assert configured.environment == "staging"
    assert configured.diddi_deployment_id == "diddigo-staging"
    assert configured.observability_metrics_token == "synthetic-metrics-token"
    assert configured.otel_logs_enabled is True


def test_otlp_log_handler_forwards_cleaned_json_record() -> None:
    class FakeLogger:
        def __init__(self) -> None:
            self.body = None

        def emit(self, **kwargs):
            self.body = kwargs["body"]

    class FakeProvider:
        def __init__(self) -> None:
            self.logger = FakeLogger()

        def get_logger(self, _name: str):
            return self.logger

    provider = FakeProvider()
    handler = OTelLogHandler(provider)
    payload = {"schema_version": "1.0.0", "event": "synthetic", "attributes": {"ok": True}}
    handler.emit(logging.LogRecord("test", logging.INFO, __file__, 1, json.dumps(payload), (), None))

    assert provider.logger.body == payload
