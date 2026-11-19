"""Updater diagnostics, isolated from root and third-party logging."""

import logging
import os
import sys


class ConsoleHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        message = record.getMessage()
        if record.levelno >= logging.WARNING:
            print(f"{record.levelname.capitalize()}: {message}", file=sys.stderr)
        else:
            print(message, flush=True)


class GitHubActionsHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.ERROR:
            level = "error"
        elif record.levelno >= logging.WARNING:
            level = "warning"
        else:
            level = "notice"

        message = record.getMessage()
        escaped = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::{level}::{escaped}", flush=True)


logger = logging.getLogger("nix_addon_manager.updater")


def configure_logging() -> None:
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler = (
        GitHubActionsHandler()
        if os.environ.get("GITHUB_ACTIONS") == "true"
        else ConsoleHandler()
    )
    for existing in logger.handlers[:]:
        logger.removeHandler(existing)
        existing.close()

    logger.addHandler(handler)


configure_logging()
