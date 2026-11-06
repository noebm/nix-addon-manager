"""Dataclass schemas and validation for installer JSON documents."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Self


def directory_name(name):
    if not isinstance(name, str) or not name or name in (".", ".."):
        raise ValueError(f"Invalid addon directory: {name!r}")
    if "/" in name or "\\" in name or ":" in name or "\0" in name:
        raise ValueError(f"Invalid addon directory: {name!r}")

    return name


@dataclass
class DownloadSource:
    """Pinned download URL, expected hash, and Nix hash algorithm."""

    url: str
    hash: str
    hashAlgorithm: str


@dataclass
class GameCompatibility:
    """Optional game flavor, release version, and addon interface version."""

    flavor: str | None = None
    version: str | None = None
    interface: int | None = None


@dataclass
class OwnedDirectory:
    """Package identity and store path recorded for an owned addon directory."""

    name: str
    version: str
    path: str

    def __post_init__(self):
        if not Path(self.path).is_absolute():
            raise ValueError("Package paths must be absolute")


@dataclass
class ManifestPackage:
    """Selected package, its installed directories, and pinned release metadata."""

    name: str
    version: str
    path: str
    directories: list[str]
    compatibility: GameCompatibility | None = None
    sources: list[DownloadSource] = field(default_factory=list)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Self:
        data = dict(value)
        compatibility = data.get("compatibility")
        data["compatibility"] = GameCompatibility(**compatibility) if compatibility is not None else None
        data["sources"] = [DownloadSource(**source) for source in data.get("sources", [])]
        return cls(**data)


@dataclass
class Manifest:
    """Schema-versioned selection evaluated from trusted Nix configuration."""

    packages: list[ManifestPackage]
    schema: int = 1

    def __post_init__(self):
        if self.schema != 1:
            raise ValueError("Unsupported manifest schema")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Self:
        if value.get("schema") != 1:
            raise ValueError("Unsupported manifest schema")

        return cls(packages=[ManifestPackage.from_dict(package) for package in value["packages"]])


@dataclass
class InstallationState:
    """Committed addon ownership and the generation protecting its store paths.

    Attributes:
        directories: Addon directory names mapped to their owning package.
        schema: Installation state format version.
        transaction: Committed transaction ID, or None before the first commit.
        game: Resolved game path, when recorded by the installer.
        manifest: Nix GC root for the committed manifest, when available.
    """

    directories: dict[str, OwnedDirectory] = field(default_factory=dict)
    schema: int = 1
    transaction: str | None = None
    game: str | None = None
    manifest: str | None = None

    def __post_init__(self):
        if self.schema != 1:
            raise ValueError("Unsupported installation state schema")

        for name in self.directories:
            directory_name(name)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Self:
        if value.get("schema") != 1:
            raise ValueError("Unsupported installation state schema")

        data = dict(value)
        data["directories"] = {name: OwnedDirectory(**owner) for name, owner in value["directories"].items()}
        return cls(**data)


@dataclass
class DirectoryChange:
    """Whether a changed addon path existed before a transaction began."""

    existed: bool

    def __post_init__(self):
        if not isinstance(self.existed, bool):
            raise ValueError("Transaction existed flag must be a boolean")


@dataclass
class TransactionJournal:
    """Transaction ID and directory changes needed to recover an interrupted apply."""

    id: str
    changes: dict[str, DirectoryChange]

    def __post_init__(self):
        # The ID is also used as a backup directory name during recovery.
        directory_name(self.id)
        for name in self.changes:
            directory_name(name)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Self:
        return cls(id=value["id"], changes={
            name: DirectoryChange(**change) for name, change in value["changes"].items()
        })


JsonDocument = Manifest | InstallationState | TransactionJournal
