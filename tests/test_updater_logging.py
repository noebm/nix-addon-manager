import io
import logging
import os
import unittest
import warnings
from unittest.mock import patch

from updater.log import configure_logging, logger


class UpdaterLoggingTests(unittest.TestCase):
    def test_own_messages_are_formatted_and_escaped(self):
        for ci in ("true", "false"):
            with (
                self.subTest(ci=ci),
                patch.dict(os.environ, {"GITHUB_ACTIONS": ci}),
                patch.object(logger, "handlers", []),
                patch("sys.stdout", new_callable=io.StringIO) as stdout,
                patch("sys.stderr", new_callable=io.StringIO) as stderr,
            ):
                configure_logging()
                logger.info("test: %s -> %s", "1%", "2")
                logger.warning("skipping\r\nrelease")

            self.assertEqual(
                stderr.getvalue(), "" if ci == "true" else "Warning: skipping\r\nrelease\n"
            )
            self.assertEqual(
                stdout.getvalue(),
                "::notice::test: 1%25 -> 2\n::warning::skipping%0D%0Arelease\n"
                if ci == "true" else "test: 1% -> 2\n",
            )

    def test_unrelated_logs_and_python_warnings_are_not_annotated(self):
        root_handler = logging.Handler()
        with (
            patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}),
            patch.object(logger, "handlers", []),
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
            patch("sys.stderr", new_callable=io.StringIO),
            patch.object(root_handler, "emit") as root_emit,
            warnings.catch_warnings(record=True) as caught,
        ):
            configure_logging()
            warnings.simplefilter("always")
            logging.getLogger().addHandler(root_handler)
            try:
                logger.info("our update")
                root_emit.assert_not_called()
                logging.getLogger("unrelated.library").warning("unrelated")
                root_emit.assert_called_once()
                warnings.warn("ordinary warning")
            finally:
                logging.getLogger().removeHandler(root_handler)

        self.assertEqual(stdout.getvalue(), "::notice::our update\n")
        self.assertEqual(len(caught), 1)
