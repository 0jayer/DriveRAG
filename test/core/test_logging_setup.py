import logging

import pytest

from rag.logging_setup import NOISY_LOGGERS, setup_logging


def test_setup_logging_sets_level_and_quiets_noisy_loggers(monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    setup_logging()

    assert logging.getLogger().level == logging.DEBUG
    for name in NOISY_LOGGERS:
        assert logging.getLogger(name).level == logging.WARNING


def test_setup_logging_writes_to_log_file(tmp_path) -> None:
    log_path = tmp_path / "logs" / "app.log"
    setup_logging(level="INFO", log_file=log_path)

    test_logger = logging.getLogger("rag.test")
    test_logger.info("hello log file")

    for handler in logging.getLogger().handlers:
        handler.flush()

    assert log_path.exists()
    assert "hello log file" in log_path.read_text(encoding="utf-8")

    logging.getLogger().handlers.clear()


def test_setup_logging_rejects_invalid_level() -> None:
    with pytest.raises(ValueError, match="Invalid log level"):
        setup_logging(level="NOT_A_LEVEL")

