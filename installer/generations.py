"""Manage an installation's generations while its installation lock is held."""

import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Generations:
    control: Path
    current: str | None

    def add(self) -> Path:
        """Prepare a fresh output path for Nix to create a generation's GC root."""
        directory = self.control / "roots"
        directory.mkdir(exist_ok=True)

        return directory / uuid.uuid4().hex

    def entries(self) -> list[Path]:
        """Include dangling generation links, which can also be removed."""
        return sorted(
            path for path in (self.control / "roots").glob("*") if path.is_symlink()
        )

    def remove(self, identifier: str) -> Path:
        """Unlink an inactive generation; its former packages become eligible for GC."""
        if (self.control / "transaction").exists():
            raise ValueError("Interrupted transaction found; run --recover first")

        matches = [
            path
            for path in self.entries()
            if identifier and path.name.startswith(identifier)
        ]
        if not matches:
            raise ValueError(f"Unknown generation ID: {identifier}")
        if len(matches) > 1:
            raise ValueError(f"Ambiguous generation ID: {identifier}")

        generation = matches[0]
        if self.current is not None and generation == Path(self.current):
            raise ValueError("Cannot remove the current generation")

        generation.unlink()
        return generation
