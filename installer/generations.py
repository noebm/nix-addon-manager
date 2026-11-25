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

    def prune(self) -> None:
        """Release inactive roots, including roots retained by older installers."""
        for generation in self.entries():
            if str(generation) != self.current:
                generation.unlink()
