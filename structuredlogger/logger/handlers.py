import logging
from logging.handlers import DatagramHandler


class SplunkHandler(DatagramHandler):
    """Send logs over UDP to Splunk."""

    def emit(self, record: logging.LogRecord) -> None:
        """Just format and encode as bytes."""
        msg = self.format(record).encode()
        self.send(msg)
