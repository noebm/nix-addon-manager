"""Describe and display changes to managed addon directories."""

from .schemas import OwnedDirectory

# Equal endpoints keep a directory; differing endpoints update it.
# An absent endpoint means installation or removal. Both cannot be absent.
type Operation = (
    tuple[OwnedDirectory, OwnedDirectory]
    | tuple[OwnedDirectory, None]
    | tuple[None, OwnedDirectory]
)


def is_unchanged(operation: Operation) -> bool:
    """Whether the installed and selected package records are equal."""
    previous, selected = operation
    return previous == selected


def generate_plan(
    previous: dict[str, OwnedDirectory],
    selected: dict[str, OwnedDirectory],
    available: set[str],
) -> dict[str, Operation]:
    """Compare package records using a snapshot of available directory names.

    Missing directories and links with missing targets must be absent from available.
    """
    plan: dict[str, Operation] = {}
    for name in sorted(previous.keys() | selected.keys()):
        if name not in selected:
            plan[name] = (previous[name], None)
        elif name not in previous or name not in available:
            plan[name] = (None, selected[name])
        else:
            plan[name] = (previous[name], selected[name])

    return plan


def display_plan(plan: dict[str, Operation]) -> None:
    """Print planned changes with their installed and selected versions."""
    for name, operation in plan.items():
        match operation:
            case _ if is_unchanged(operation):
                continue
            case (None, OwnedDirectory(version=version)):
                action = "install"
            case (OwnedDirectory(version=version), None):
                action = "remove"
            case (OwnedDirectory(version=previous), OwnedDirectory(version=selected)):
                action = "update"
                version = f"{previous} -> {selected}"

        print(f"{action}: {name} {version}", flush=True)
