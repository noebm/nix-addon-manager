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
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field, replace
from functools import wraps
from inspect import isfunction
from pathlib import Path
from typing import TextIO

from .client import discover_clients, validate_compatibility
from .delta import Operation, display_plan, generate_plan, is_unchanged
from .generations import Generations
from .installations import (
    installation_id,
    state_directory,
    validate_game_path,
)
from .schemas import (
    DirectoryChange,
    InstallationState,
    Manifest,
    OwnedDirectory,
    TransactionJournal,
    directory_name,
)
from .storage import write_json


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


def validate_managed_links(
    target: Path,
    previous: dict[str, OwnedDirectory],
    selected: dict[str, OwnedDirectory],
) -> None:
    """Reject unmanaged conflicts and changes to recorded addon links."""
    existing = {path.name.casefold(): path.name for path in target.iterdir()}
    for name in sorted(previous.keys() | selected.keys()):
        destination = target / name
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
            raise ValueError("Interrupted transaction found; run recover first")

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
            raise ValueError("Interrupted transaction found; run recover first")

        validate_compatibility(installation.game, manifest)
        selected = selected_directories(manifest)
        state = self.state()
        previous = state.directories

        validate_managed_links(installation.target, previous, selected)

        available = {name for name in previous if (installation.target / name).exists()}
        plan = generate_plan(previous, selected, available)

        if not apply:
            return plan

        if all(is_unchanged(operation) for operation in plan.values()):
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
            for name, operation in plan.items()
            if not is_unchanged(operation)
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
        f"installationFile = {nix_string(configuration)}; "
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


@contextmanager
def saved_generations(state_dir: Path, *, prune: bool = False):
    """Access saved generations without requiring the game to still exist."""
    if state_dir.is_symlink():
        raise ValueError("Manager state directory must not be a symlink")

    fd = os.open(state_dir / "lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError(
                "Another installer is operating on this game directory"
            ) from None

        if (state_dir / "transaction").exists():
            raise ValueError("Interrupted transaction found; run recover first")

        state_path = state_dir / "state.json"
        state = (
            InstallationState.from_dict(json.loads(state_path.read_text()))
            if state_path.exists()
            else InstallationState()
        )
        current = state.manifest
        if prune and state.game is not None and not Path(state.game).exists():
            current = None

        yield Generations(state_dir, current)


def handle_generations(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> None:
    root = state_directory()
    if args.game_path is not None:
        game = args.game_path.expanduser().resolve()
        state_dir = root / installation_id(game)
        state_dirs = [state_dir] if state_dir.exists() else []
    else:
        state_dirs = sorted(
            state_dir
            for state_dir in root.glob("*")
            if len(state_dir.name) == 64
            and all(character in "0123456789abcdef" for character in state_dir.name)
            and state_dir.is_dir()
        )

    # ExitStack keeps all installation locks held for global generation commands
    # without changing the per-installation state schema.
    # FIXME: Manage generations from a single state description.
    with ExitStack() as stack:
        installations = [
            stack.enter_context(
                saved_generations(state_dir, prune=args.generation_action == "prune")
            )
            for state_dir in state_dirs
        ]
        entries = [
            (install_generations, generation)
            for install_generations in installations
            for generation in install_generations.entries()
        ]
        match args.generation_action:
            case "prune":
                inactive = [
                    (install_generations, generation)
                    for install_generations, generation in entries
                    if str(generation) != install_generations.current
                ]
                for install_generations, generation in inactive:
                    install_generations.remove(generation.name)
                    print(f"Removed generation: {generation.name}")

                if not inactive:
                    print("No old generations")
            case "remove":
                matches = [
                    (install_generations, generation)
                    for install_generations, generation in entries
                    if args.id and generation.name.startswith(args.id)
                ]
                if not matches:
                    raise ValueError(f"Unknown generation ID: {args.id}")
                if len(matches) > 1:
                    raise ValueError(f"Ambiguous generation ID: {args.id}")

                install_generations, generation = matches[0]
                removed = install_generations.remove(generation.name)
                print(f"Removed generation: {removed.name}")
            case "list":
                print("Generations:")
                if not entries:
                    print("  No generations")

                for install_generations, generation in entries:
                    marker = (
                        " (current)"
                        if str(generation) == install_generations.current
                        else ""
                    )
                    print(
                        f"  {generation.name}{marker} -> {generation.readlink()} "
                        f"(installation {install_generations.control.name})"
                    )
            case _:
                parser.error(f"Unknown generations action: {args.generation_action}")


def main():
    parser = argparse.ArgumentParser(prog="nix-addon-manager", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    discover = commands.add_parser(
        "discover", help="Locate local game installations for addons.nix"
    )
    discover.add_argument(
        "paths", nargs="*", type=Path, help="Directories to search (default: home)"
    )

    update = commands.add_parser("update", help="Preview or apply an addon selection")
    update.add_argument(
        "config", type=Path, help="Nix function returning gamePath and addons"
    )
    # MIGRATION (manifest schema 1 -> 2): recognize the removed update option
    # only for guidance; remove together with its error below and migration test.
    update.add_argument("--game-path", dest="removed_game_path", help=argparse.SUPPRESS)
    update.add_argument(
        "--apply", action="store_true", help="Build, stage, and install the selection"
    )

    export = commands.add_parser(
        "export", help="Build and export an addon selection as a ZIP"
    )
    export.add_argument(
        "config", type=Path, help="Nix function returning gamePath and addons"
    )
    export.add_argument(
        "--output", type=Path, required=True, help="Destination ZIP path"
    )

    recover = commands.add_parser("recover", help="Recover an interrupted transaction")
    recover.add_argument(
        "target", type=Path, help="Nix configuration or game directory"
    )

    generations = commands.add_parser(
        "generations", help="Manage installation generations"
    )
    generation_commands = generations.add_subparsers(
        dest="generation_action", required=True
    )
    listing = generation_commands.add_parser("list")
    pruning = generation_commands.add_parser(
        "prune",
        help="Remove all inactive generation roots (keeps the current generation)",
    )
    removal = generation_commands.add_parser("remove")
    removal.add_argument("id", help="Generation ID or unique prefix")
    for command in (listing, pruning, removal):
        command.add_argument(
            "--game-path",
            type=Path,
            help="Game directory",
        )

    args = parser.parse_args()

    # MIGRATION (manifest schema 1 -> 2): remove with the hidden option above.
    if args.command == "update" and args.removed_game_path is not None:
        update.error(
            "--game-path is no longer supported for update; "
            'set gamePath = "/path/to/WoW/_forever_"; in your Nix configuration '
            "and remove --game-path from the command"
        )

    try:
        if args.command == "discover":
            clients = discover_clients(args.paths or [Path.home()])
            for game, client in clients:
                path = json.dumps(str(game), ensure_ascii=False).replace("${", "\\${")
                print(f"# {client.flavor} (interface {client.interface})")
                print(f"gamePath = {path};")

            if not clients:
                print("No installations found")
            return

        if args.command == "generations":
            handle_generations(args, parser)
            return

        repository = Path(__file__).resolve().parents[1]

        if args.command == "export":
            if os.path.lexists(args.output):
                raise FileExistsError(
                    errno.EEXIST, os.strerror(errno.EEXIST), args.output
                )

            configuration = args.config.resolve(strict=True)
            # Keep the build rooted until all package contents have been archived.
            with tempfile.TemporaryDirectory(prefix="addon-export-") as temporary:
                manifest = nix_manifest(
                    repository,
                    configuration,
                    out_link=Path(temporary) / "manifest",
                )
                export_zip(manifest, args.output.absolute())
            for package in manifest.packages:
                print(f"exported: {package.name} {package.version}")

            print(f"Export complete: {args.output}")
            return

        if args.command == "update":
            configuration = args.config.resolve(strict=True)
            manifest = nix_manifest(repository, configuration)
            game_path = Path(manifest.gamePath).expanduser()
        else:
            target = args.target.expanduser().resolve(strict=True)
            if target.is_dir():
                game_path = target
            else:
                manifest = nix_manifest(repository, target)
                game_path = Path(manifest.gamePath).expanduser()

        installation = Installation(game_path)
        with installation.lock() as locked:
            if args.command == "recover":
                if (
                    not installation.state_path.exists()
                    and not installation.transaction.exists()
                ):
                    raise ValueError(
                        "No managed addon installation or pending transaction to recover"
                    )

                locked.recover()
                print("Recovery complete")
                return

            plan = locked.reconcile(manifest)
            display_plan(plan)

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
