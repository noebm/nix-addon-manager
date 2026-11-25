"""Shared persistence helpers for installer documents."""

import json
import os
from dataclasses import asdict
from pathlib import Path

from .schemas import JsonDocument


def write_json(path: Path, value: JsonDocument) -> None:
    temporary = path.with_suffix(".tmp")
    with temporary.open("w") as stream:
        json.dump(asdict(value), stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())

    temporary.replace(path)
