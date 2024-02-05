# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Centralized setup of logging for the service."""
import logging.config
import os
from inspect import getframeinfo, stack

import structlog


class FileNameRenderer(object):
    """File name Renderer."""

    def __init__(self, stack_depth):
        self._stack_depth = stack_depth

    def __call__(self, logger, name, event_dict):
        caller = getframeinfo(stack()[self._stack_depth][0])

        event_dict["file_name"] = f"{caller.filename}:{caller.lineno}"
        return event_dict


def setup_logging():
    """Set logging."""
    pre_chain = [
        # Add the log level and a timestamp to the event_dict if the log entry
        # is not from structlog.
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    # logging_client = google.cloud.logging.Client()
    # logging_client.setup_logging()

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "plain": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(colors=False),
                    "foreign_pre_chain": pre_chain,
                    "keep_exc_info": True,
                    "keep_stack_info": True,
                },
                "json_formatter": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.processors.JSONRenderer(),
                },
                "colored": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(colors=True),
                },
                "key_value": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.processors.KeyValueRenderer(
                        key_order=["timestamp", "level", "event", "logger"]
                    ),
                },
            },
            "handlers": {
                "consoleHandler": {
                    "class": "logging.StreamHandler",
                    "formatter": "plain",
                },
                "cloudHandler": {
                    "class": "logging.StreamHandler",
                    "formatter": "json_formatter",
                },
            },
            "loggers": {
                "notify_api": {
                    "handlers": ["cloudHandler"],
                    "level": os.environ.get("LOG_LEVEL", "INFO"),
                    "propagate": False,
                },
                "werkzeug": {
                    "handlers": ["consoleHandler"],
                    "level": os.environ.get("LOG_LEVEL", "WARNING"),
                    "propagate": False,
                },
            },
        }
    )

    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.format_exc_info,
            structlog.processors.StackInfoRenderer(),
            FileNameRenderer(stack_depth=5),
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
