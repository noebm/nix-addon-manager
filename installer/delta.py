"""Describe and display changes to managed addon directories."""

from enum import Enum

from .schemas import OwnedDirectory


class Operation(Enum):
    """Action planned for a managed addon directory."""

    INSTALL = "install"
    UPDATE = "update"
    REMOVE = "remove"
    KEEP = "keep"


def display_plan(
    plan: dict[str, Operation],
    previous: dict[str, OwnedDirectory],
    selected: dict[str, OwnedDirectory],
) -> None:
    """Print planned changes with their installed and selected versions."""
    for name, operation in plan.items():
        if operation is Operation.KEEP:
            continue

        if operation is Operation.UPDATE:
            version = f"{previous[name].version} -> {selected[name].version}"
        elif operation is Operation.REMOVE:
            version = previous[name].version
        else:
            version = selected[name].version

        print(f"{operation.value}: {name} {version}", flush=True)
