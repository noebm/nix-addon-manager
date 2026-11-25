"""Game path validation and per-installation state locations."""

import hashlib
import os
from pathlib import Path


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
