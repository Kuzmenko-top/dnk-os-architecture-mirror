# --- DNK-MRH-HEADER ---
# mrh_id: "tests/monitoring/test_logging.py"
# purpose: "Test suite for structured JSON logging utilities"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import logging
import pytest
from dnk_os.utils.logging import JSONFormatter, setup_logging


class TestStructuredLogging:
    """Test suite for structured JSON logging."""

    def test_json_formatter_output(self):
        """Test JSONFormatter converts LogRecord to valid JSON with metadata."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="dnk_os.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=25,
            msg="Test log message %s",
            args=("param1",),
            exc_info=None
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "dnk_os.test"
        assert parsed["message"] == "Test log message param1"
        assert "timestamp" in parsed
        assert parsed["line"] == 25

    def test_json_formatter_exception(self):
        """Test JSONFormatter captures exception traceback."""
        formatter = JSONFormatter()
        try:
            raise ValueError("Sample test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="dnk_os.error",
                level=logging.ERROR,
                pathname=__file__,
                lineno=45,
                msg="Error occurred",
                args=(),
                exc_info=exc_info
            )
            output = formatter.format(record)
            parsed = json.loads(output)
            assert parsed["level"] == "ERROR"
            assert "exception" in parsed
            assert "ValueError: Sample test error" in parsed["exception"]

    def test_setup_logging(self):
        """Test setup_logging configures logger level and JSONFormatter."""
        logger = setup_logging(level="DEBUG")
        assert logger.name == "dnk_os"
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) >= 1
        assert any(isinstance(h.formatter, JSONFormatter) for h in logger.handlers)
