from __future__ import annotations

import json
import logging
import logging.config
from copy import deepcopy

import pytest
from uvicorn.config import LOGGING_CONFIG

from app_base.core.settings import Settings
from app_base.core.telemetry import OTelLogHandler, _install_otel_log_handler

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


def test_uvicorn_error_uses_one_otlp_handler_without_duplicates() -> None:
    class FakeLogger:
        def __init__(self) -> None:
            self.emitted = []

        def emit(self, **kwargs):
            self.emitted.append(kwargs)

    class FakeProvider:
        def __init__(self) -> None:
            self.logger = FakeLogger()

        def get_logger(self, _name: str):
            return self.logger

    logging.config.dictConfig(deepcopy(LOGGING_CONFIG))
    logger = logging.getLogger("uvicorn.error")
    provider = FakeProvider()

    _install_otel_log_handler(provider)
    _install_otel_log_handler(provider)
    otel_handlers = [handler for handler in logger.handlers if getattr(handler, "_diddigo_otel_handler", False)]

    logger.info(json.dumps({"schema_version": "1.0.0", "event": "uvicorn.test"}))

    assert len(otel_handlers) == 1
    assert len(provider.logger.emitted) == 1
    assert provider.logger.emitted[0]["body"]["event"] == "uvicorn.test"
