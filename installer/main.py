"""Install Nix-built addon directories without owning any game settings."""

import argparse
import errno
import fcntl
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
import zipfile
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, replace
from enum import Enum
from functools import wraps
from inspect import isfunction
from pathlib import Path
from typing import TextIO

from .client import validate_compatibility
from .generations import Generations
from .installations import (
    InstallationRegistry,
    installation_id,
    state_directory,
    validate_game_path,
)
from .schemas import (
    DirectoryChange,
    InstallationState,
    JsonDocument,
    Manifest,
    OwnedDirectory,
    TransactionJournal,
    directory_name,
)


def write_json(path: Path, value: JsonDocument) -> None:
    temporary = path.with_suffix(".tmp")
    with temporary.open("w") as stream:
        json.dump(asdict(value), stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())

    temporary.replace(path)


def selected_directories(manifest: Manifest) -> dict[str, OwnedDirectory]:
    selected = {}
    names = set()
    for package in manifest.packages:
        owner = OwnedDirectory(package.name, package.version, package.path)
        for name in package.directories:
            directory_name(name)
            if name.casefold() in names:
                raise ValueError(f"Conflicting directory ownership: {name}")

            names.add(name.casefold())
            selected[name] = owner

    return selected


def validate_tree(root):
    # Link only validated package trees; reject internal links and special files.
    mode = root.lstat().st_mode
    if not stat.S_ISDIR(mode):
        raise ValueError(f"Expected a real addon directory: {root}")

    for path in root.rglob("*"):
        mode = path.lstat().st_mode
        if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise ValueError(f"Unsafe package content: {path}")


def remove_tree(root):
    if root.is_symlink():
        root.unlink()
        return

    shutil.rmtree(root)


def move_link(source, destination):
    try:
        source.rename(destination)
    except OSError as error:
        if error.errno != errno.EXDEV:
            raise

        destination.symlink_to(source.readlink(), target_is_directory=True)
        source.unlink()


@dataclass(eq=False)
class Installation:
    """Describe a game installation and provide access through lock().

    Attributes:
        game: Resolved game directory containing Interface/AddOns.
        target: Directory where managed addon symlinks are installed.
        control: Per-game state directory outside the game, holding state,
            backups, and generation links.
        transaction: Pending transaction directory containing its journal,
            staged links, and previous links for recovery.
        state_path: JSON record of owned addon directories and the committed
            manifest generation.
    """

    game: Path
    target: Path = field(init=False)
    control: Path = field(init=False)
    transaction: Path = field(init=False)
    state_path: Path = field(init=False)

    def __post_init__(self):
        self.game = validate_game_path(Path(self.game))
        self.target = self.game / "Interface/AddOns"

        self.control = state_directory() / installation_id(self.game)
        if self.control.is_symlink():
            raise ValueError("Manager state directory must not be a symlink")

        if self.control.resolve().is_relative_to(self.game):
            raise ValueError("Manager state must be outside the game directory")

        self.control.mkdir(parents=True, exist_ok=True)
        self.transaction = self.control / "transaction"
        self.state_path = self.control / "state.json"

    @contextmanager
    def lock(self):
        """Yield a LockedInstallation valid only while this context holds the lock."""
        fd = os.open(
            self.control / "lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
        )
        with os.fdopen(fd, "w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError(
                    "Another installer is operating on this game directory"
                ) from None

            yield LockedInstallation(self, lock)


def requires_active_lock(cls):
    """Guard public instance methods defined on cls using its _lock file.

    Private methods, properties, and inherited methods are left unchanged.
    The lock file must remain open only for the lifetime of the lock context.
    """

    def guard(method):
        @wraps(method)
        def checked(self, *args, **kwargs):
            if self._lock.closed:
                raise RuntimeError("Installation lock context has exited")

            return method(self, *args, **kwargs)

        return checked

    for name, method in list(vars(cls).items()):
        if not name.startswith("_") and isfunction(method):
            setattr(cls, name, guard(method))

    return cls


class Operation(Enum):
    """Action planned for a managed addon directory."""

    INSTALL = "install"
    UPDATE = "update"
    REMOVE = "remove"
    KEEP = "keep"


@requires_active_lock
@dataclass(eq=False)
class LockedInstallation:
    """Access installation state and transactions while its lock is held.

    Obtain instances through Installation.lock(). Each instance expires when
    its context exits; acquiring a new lock does not reactivate old instances.
    The class decorator checks the lock before every public method call.

    Attributes:
        _installation: Paths of the installation protected by this context.
        _lock: Open file holding this context's lock; closure marks expiry.
    """

    _installation: Installation
    _lock: TextIO = field(repr=False)

    def state(self) -> InstallationState:
        installation = self._installation

        if not installation.state_path.exists():
            return InstallationState()

        return InstallationState.from_dict(
            json.loads(installation.state_path.read_text())
        )

    def generations(self) -> Generations:
        """Access generations using the currently committed installation state."""
        if self._installation.transaction.exists():
            raise ValueError("Interrupted transaction found; run --recover first")

        return Generations(self._installation.control, self.state().manifest)

    def _archive_transaction(self, identifier: str) -> None:
        installation = self._installation

        backups = installation.control / "backups"
        backups.mkdir(exist_ok=True)
        installation.transaction.rename(backups / identifier)

    def recover(self) -> None:
        installation = self._installation

        if not installation.transaction.exists():
            return

        journal_path = installation.transaction / "journal.json"
        if not journal_path.exists():
            # No changes to AddOns occur until the journal has been published.
            remove_tree(installation.transaction)
            return

        journal = TransactionJournal.from_dict(json.loads(journal_path.read_text()))
        if self.state().transaction == journal.id:
            self._archive_transaction(journal.id)
            return

        for name, change in journal.changes.items():
            directory_name(name)
            destination = installation.target / name
            backup = installation.transaction / "previous" / name
            if backup.exists() or backup.is_symlink():
                if destination.exists() or destination.is_symlink():
                    remove_tree(destination)
                move_link(backup, destination)
            elif not change.existed and destination.is_symlink():
                remove_tree(destination)

        remove_tree(installation.transaction)

    def reconcile(
        self,
        manifest: Manifest,
        *,
        apply: bool = False,
        manifest_root: Path | None = None,
    ) -> dict[str, Operation]:
        installation = self._installation

        if installation.transaction.exists():
            raise ValueError("Interrupted transaction found; run --recover first")

        validate_compatibility(installation.game, manifest)
        selected = selected_directories(manifest)
        state = self.state()
        previous = state.directories
        existing = {
            path.name.casefold(): path.name for path in installation.target.iterdir()
        }
        plan = {}
        for name in sorted(previous.keys() | selected.keys()):
            destination = installation.target / name
            actual = existing.get(name.casefold())
            if actual is not None and (name not in previous or actual != name):
                raise ValueError(
                    f"Unmanaged directory conflict: {actual}; move it aside explicitly"
                )
            if destination.is_symlink():
                expected = Path(previous[name].path) / "share/wow-addons" / name
                if destination.readlink() != expected:
                    raise ValueError(f"Unexpected managed link target: {destination}")
            elif destination.exists():
                raise ValueError(f"Expected a managed symlink: {destination}")

            if name not in selected:
                plan[name] = Operation.REMOVE
            elif name not in previous or not destination.exists():
                plan[name] = Operation.INSTALL
            else:
                plan[name] = (
                    Operation.KEEP
                    if previous[name] == selected[name]
                    else Operation.UPDATE
                )

        if not apply:
            return plan

        if all(action is Operation.KEEP for action in plan.values()):
            if manifest_root is not None:
                write_json(
                    installation.state_path,
                    replace(
                        state,
                        game=str(installation.game),
                        manifest=str(manifest_root),
                    ),
                )
            return plan

        identifier = uuid.uuid4().hex
        installation.transaction.mkdir()
        staged = installation.transaction / "staged"
        backups = installation.transaction / "previous"
        staged.mkdir()
        backups.mkdir()
        changes = {
            name: DirectoryChange(
                existed=(installation.target / name).exists()
                or (installation.target / name).is_symlink(),
            )
            for name, action in plan.items()
            if action is not Operation.KEEP
        }
        try:
            for name in changes:
                if name in selected:
                    source = Path(selected[name].path) / "share/wow-addons" / name
                    validate_tree(source)
                    (staged / name).symlink_to(source, target_is_directory=True)

            write_json(
                installation.transaction / "journal.json",
                TransactionJournal(identifier, changes),
            )
            for name, change in changes.items():
                if change.existed:
                    move_link(installation.target / name, backups / name)
                if name in selected:
                    move_link(staged / name, installation.target / name)

            write_json(
                installation.state_path,
                InstallationState(
                    transaction=identifier,
                    directories=selected,
                    game=str(installation.game),
                    manifest=str(manifest_root) if manifest_root else None,
                ),
            )
        except BaseException:
            self.recover()
            raise

        self._archive_transaction(identifier)
        return plan


def nix_manifest(
    repository: Path, configuration: Path, *, out_link: Path | None = None
) -> Manifest:
    """Evaluate the selection, or build it with a GC root at out_link."""

    def nix_string(value):
        return json.dumps(str(value)).replace("${", "\\${")

    build = out_link is not None
    expression = (
        f"import (builtins.toPath {nix_string(repository / 'lib/manifest.nix')}) {{ "
        f"repository = {nix_string(repository)}; "
        f"configuration = {nix_string(configuration)}; "
        f"build = {'true' if build else 'false'}; }}"
    )
    command = [
        "nix",
        "build" if build else "eval",
        "--impure",
        "--json",
        "--expr",
        expression,
    ]
    if out_link is not None:
        command.extend(["--out-link", str(out_link)])

    result = json.loads(subprocess.check_output(command, text=True))
    if build:
        return Manifest.from_dict(
            json.loads(Path(result[0]["outputs"]["out"]).read_text())
        )

    return Manifest.from_dict(result)


def export_zip(manifest: Manifest, destination: Path) -> None:
    """Publish a compressed, standalone addon set without replacing existing files."""
    selected = selected_directories(manifest)
    sources = {
        name: Path(owner.path) / "share/wow-addons" / name
        for name, owner in selected.items()
    }
    for source in sources.values():
        validate_tree(source)

    with tempfile.TemporaryDirectory(
        prefix=".addon-export-", dir=destination.parent
    ) as temporary:
        archive_path = Path(temporary) / "addons.zip"
        with zipfile.ZipFile(
            archive_path, "w", compression=zipfile.ZIP_DEFLATED, strict_timestamps=False
        ) as archive:
            for name, source in sorted(sources.items()):
                archive.write(source, name)
                for path in sorted(source.rglob("*")):
                    archive.write(path, str(Path(name) / path.relative_to(source)))

        # Publish only a complete archive, and never overwrite another export.
        os.link(archive_path, destination)


def handle_installations(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> None:
    if args.game_path or args.export_zip or args.config or args.apply or args.recover:
        parser.error(
            "installations commands cannot be combined with installation options"
        )

    registry = InstallationRegistry.from_environment()

    def display(installation):
        return registry.format_installation(installation, full=args.full)

    match args.installation_action:
        case "list":
            installations = registry.list_installations()
            print("Installations:")
            if not installations:
                print("  No installations registered")

            for installation, is_default in installations:
                marker = " (default)" if is_default else ""
                print(f"  {display(installation)}{marker}")
        case "add":
            added = registry.add(Path(args.path))
            print(f"Installation {display(added)} has been added")
        case "default":
            if args.path is None:
                game_path = registry.default_game_path
                if game_path is None:
                    print("error: No default installation", file=sys.stderr)
                    sys.exit(1)

                print(game_path)
            else:
                selected = registry.set_default(args.path)
                if selected is None:
                    print(
                        f"error: Installation is not registered: {args.path}",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                print(f"Installation {display(selected)} has been set as default")
        case "remove":
            removed = registry.remove(args.path)
            if removed is None:
                print(f"Installation {args.path} is already absent")
            else:
                print(f"Installation {display(removed)} has been removed")
        case _:
            parser.error(f"Unknown installations action: {args.installation_action}")


def handle_generations(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> None:
    if args.export_zip or args.config or args.apply or args.recover:
        parser.error(
            "generations commands cannot be combined with installation actions"
        )
    registry = InstallationRegistry.from_environment()
    selection = args.game_path
    game = (
        registry.resolve_game_path(selection)
        if selection is not None
        else registry.default_game_path
    )
    if game is None:
        raise ValueError("No default installation; use --game-path")

    installation = Installation(game)
    with installation.lock() as locked:
        generations = locked.generations()
        match args.generation_action:
            case "prune":
                inactive = [
                    generation
                    for generation in generations.entries()
                    if str(generation) != generations.current
                ]
                for generation in inactive:
                    generations.remove(generation.name)
                    print(f"Removed generation: {generation.name}")

                if not inactive:
                    print("No old generations")
            case "remove":
                removed = generations.remove(args.id)
                print(f"Removed generation: {removed.name}")
            case "list":
                entries = generations.entries()
                print("Generations:")
                if not entries:
                    print("  No generations")

                for generation in entries:
                    marker = (
                        " (current)" if str(generation) == generations.current else ""
                    )
                    print(f"  {generation.name}{marker} -> {generation.readlink()}")
            case _:
                parser.error(f"Unknown generations action: {args.generation_action}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command")
    generations = commands.add_parser(
        "generations", help="Manage installation generations"
    )
    generation_commands = generations.add_subparsers(
        dest="generation_action", required=True
    )
    generation_commands.add_parser("list")
    generation_commands.add_parser(
        "prune",
        help="Remove all inactive generation roots (keeps the current generation)",
    )
    removal = generation_commands.add_parser("remove")
    removal.add_argument("id", help="Generation ID or unique prefix")
    installations = commands.add_parser(
        "installations", help="Manage registered game installations"
    )
    installation_commands = installations.add_subparsers(
        dest="installation_action", required=True
    )
    for name in ("add", "remove", "default"):
        command = installation_commands.add_parser(name)
        command.add_argument(
            "--full", action="store_true", help="Show complete installation IDs"
        )
        command.add_argument(
            "path",
            nargs="?" if name == "default" else None,
            help="Game directory"
            if name == "add"
            else "Game directory or unique installation ID prefix",
        )
    listing = installation_commands.add_parser("list")
    listing.add_argument(
        "--full", action="store_true", help="Show complete installation IDs"
    )

    target = parser.add_mutually_exclusive_group()
    target.add_argument("--game-path", type=Path)
    target.add_argument(
        "--export-zip",
        type=Path,
        metavar="PATH",
        help="Build and export the selection as a compressed ZIP",
    )
    parser.add_argument(
        "--config", type=Path, help="Nix function returning an addon package list"
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--apply", action="store_true", help="Build, stage, and install the selection"
    )
    action.add_argument(
        "--recover", action="store_true", help="Recover an interrupted transaction"
    )
    args = parser.parse_args()
    if args.command is None and not args.recover and args.config is None:
        parser.error("--config is required unless using --recover")

    if args.export_zip is not None and (args.apply or args.recover):
        parser.error("--export-zip cannot be combined with --apply or --recover")

    try:
        if args.command == "installations":
            handle_installations(args, parser)

            return

        if args.command == "generations":
            handle_generations(args, parser)
            return

        repository = Path(__file__).resolve().parents[1]

        if args.export_zip is not None:
            if os.path.lexists(args.export_zip):
                raise FileExistsError(
                    errno.EEXIST, os.strerror(errno.EEXIST), args.export_zip
                )

            configuration = args.config.resolve(strict=True)
            # Keep the build rooted until all package contents have been archived.
            with tempfile.TemporaryDirectory(prefix="addon-export-") as temporary:
                manifest = nix_manifest(
                    repository,
                    configuration,
                    out_link=Path(temporary) / "manifest",
                )
                export_zip(manifest, args.export_zip.absolute())
            for package in manifest.packages:
                print(f"exported: {package.name} {package.version}")

            print(f"Export complete: {args.export_zip}")
            return

        registry = InstallationRegistry.from_environment()
        game_path = (
            registry.resolve_game_path(args.game_path)
            if args.game_path is not None
            else registry.default_game_path
        )
        if game_path is None:
            print(
                "error: No default installation; use installations default or --game-path",
                file=sys.stderr,
            )
            sys.exit(1)

        installation = Installation(game_path)
        with installation.lock() as locked:
            if args.recover:
                locked.recover()
                print("Recovery complete")
                return

            configuration = args.config.resolve(strict=True)
            manifest = nix_manifest(repository, configuration)
            plan = locked.reconcile(manifest)
            for name, operation in plan.items():
                print(f"{operation.value}: {name}", flush=True)

            if args.apply:
                generations = locked.generations()
                root = generations.add()
                # Keep every generation rooted, including interrupted operations and backups.
                built = nix_manifest(repository, configuration, out_link=root)
                if built != manifest:
                    raise ValueError(
                        "Configuration changed during build; preview again"
                    )
                locked.reconcile(built, apply=True, manifest_root=root)
                print("Installation complete")
            else:
                print("Preview only; pass --apply to install")
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
