import ast
import logging
import logging.config

import structlog
from pythonjsonlogger import jsonlogger
from structlog.dev import ConsoleRenderer


class PlainFormatter(logging.Formatter):
    def format(self, record):
        record.message = ast.literal_eval(record.getMessage()).pop("message")
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        s = self.formatMessage(record)
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + record.exc_text
        if record.stack_info:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + self.formatStack(record.stack_info)
        return s


def format_message(_, __, event_dict):
    template = event_dict['event']
    event_dict['message'] = template.format(**event_dict)
    return event_dict


def initialize():
    time_stamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
    pre_chain = [
        # Add the log level and a timestamp to the event_dict if the log entry
        # is not from structlog.
        structlog.stdlib.add_log_level,
        time_stamper,
        format_message,
    ]

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {
                "()": PlainFormatter,
                "format": "%(asctime)s.%(msecs)03dZ - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S"
            },
            "colored": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": ConsoleRenderer(colors=True),
                "foreign_pre_chain": pre_chain,
            },
            "json": {
                "()": jsonlogger.JsonFormatter
            }
        },
        "handlers": {
            "default": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "colored",
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.handlers.WatchedFileHandler",
                "filename": "test.log",
                "formatter": "plain",
            },
            "splunk": {
                "level": "INFO",
                "class": "structuredlogger.logger.handlers.SplunkHandler",
                "host": "127.0.0.1",
                "port": 514,
                "formatter": "json",
            }
        },
        "loggers": {
            "": {
                "handlers": ["default", "file", "splunk"],
                "level": "DEBUG",
                "propagate": True,
            },
        }
    })

    structlog.configure_once(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            time_stamper,
            format_message,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name):
    logger = structlog.get_logger(name)
    logger = logger.bind(execution_id=999)
    return logger
