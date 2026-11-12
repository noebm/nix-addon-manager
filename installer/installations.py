"""Persistent installation registration and default selection."""

import fcntl
import hashlib
import json
import os
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Self

from .schemas import RegisteredInstallation, RegistryDocument


@dataclass(frozen=True)
class InstallationPath:
    identifier: str
    game_path: Path

    def __str__(self) -> str:
        return f"{self.game_path} ({self.identifier})"


def state_directory() -> Path:
    state_home = Path.home() / ".local/state"
    xdg_state_home = os.environ.get("XDG_STATE_HOME")

    # NOTE: XDG_STATE_HOME must be absolute to be considered valid.
    if xdg_state_home and Path(xdg_state_home).is_absolute():
        state_home = Path(xdg_state_home)

    return state_home / "nix-addon-manager"


def installation_id(game: Path) -> str:
    return hashlib.sha256(os.fsencode(game)).hexdigest()


def validate_game_path(game_path: Path) -> Path:
    game_path = game_path.expanduser().resolve(strict=True)
    target = game_path / "Interface/AddOns"
    if not target.is_dir() or target.resolve() != target:
        raise ValueError("Game path must contain real Interface/AddOns directories")
    if state_directory().resolve().is_relative_to(game_path):
        raise ValueError("Manager state must be outside the game directory")

    return game_path


@dataclass
class InstallationRegistry:
    """Read and edit the registry document under a registry lock."""

    _root: Path
    _document: RegistryDocument = field(default_factory=RegistryDocument)

    @classmethod
    def from_environment(cls) -> Self:
        registry = cls(state_directory())
        registry._read()
        return registry

    @property
    def _document_path(self) -> Path:
        return self._root / "installations.json"

    def _read(self) -> None:
        self._document = (
            RegistryDocument.from_dict(json.loads(self._document_path.read_text()))
            if self._document_path.exists()
            else RegistryDocument()
        )

    @contextmanager
    def edit(self):
        self._root.mkdir(parents=True, exist_ok=True)
        fd = os.open(
            self._root / "installations.lock",
            os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW,
            0o600,
        )
        with os.fdopen(fd, "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self._read()
            yield self

            temporary = self._document_path.with_suffix(".tmp")
            with temporary.open("w") as stream:
                json.dump(asdict(self._document), stream, indent=2)
                stream.flush()
                os.fsync(stream.fileno())

            temporary.replace(self._document_path)

    def _resolve_identifier(self, value: str) -> str | None:
        if value in self._document.installations:
            return value

        identifier = installation_id(Path(value).expanduser().resolve())
        if identifier not in self._document.installations:
            return None

        return identifier

    def resolve_game_path(self, value: Path) -> Path:
        entry = self._document.installations.get(str(value))
        return Path(entry.game) if entry else value.expanduser()

    @property
    def default_game_path(self) -> Path | None:
        identifier = self._document.default
        if identifier is None:
            return None

        return Path(self._document.installations[identifier].game)

    def list_installations(self) -> list[tuple[InstallationPath, bool]]:
        """Return installation IDs, game paths, and whether each is the default."""
        return [
            (
                InstallationPath(identifier, Path(entry.game)),
                identifier == self._document.default,
            )
            for identifier, entry in sorted(self._document.installations.items())
        ]

    def add(self, path: Path) -> InstallationPath:
        game = validate_game_path(path)
        identifier = installation_id(game)
        with self.edit():
            self._document.installations[identifier] = RegisteredInstallation(
                game=str(game),
            )

        return InstallationPath(identifier, game)

    def set_default(self, path: str) -> InstallationPath | None:
        with self.edit():
            identifier = self._resolve_identifier(path)
            if identifier is None:
                return None

            self._document.default = identifier
            game = Path(self._document.installations[identifier].game)

        return InstallationPath(identifier, game)

    def remove(self, path: str) -> InstallationPath | None:
        with self.edit():
            identifier = self._resolve_identifier(path)
            if identifier is None:
                return None

            entry = self._document.installations.pop(identifier)
            if self._document.default == identifier:
                self._document.default = None

        return InstallationPath(identifier, Path(entry.game))
