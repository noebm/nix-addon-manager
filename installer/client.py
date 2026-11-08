"""Read local Blizzard client metadata and check declared addon compatibility."""

import csv
from pathlib import Path
import re
import sys

from .schemas import GameCompatibility, Manifest


def detect_client(game: Path) -> GameCompatibility:
    """Select the active build for this client's product, without running it."""
    flavor_path = game / ".flavor.info"
    if not flavor_path.is_file():
        raise ValueError(f"Cannot detect game product: missing {flavor_path}")

    flavor_rows = flavor_path.read_text(encoding="utf-8-sig").strip().splitlines()
    if flavor_rows and flavor_rows[0] == "Product Flavor!STRING:0":
        flavor_rows = flavor_rows[1:]

    if len(flavor_rows) != 1 or not re.fullmatch(r"[a-z0-9_]+", flavor_rows[0]):
        raise ValueError(f"Invalid game product in {flavor_path}")

    product = flavor_rows[0]
    build_path = next((root / ".build.info" for root in (game, game.parent)
                       if (root / ".build.info").is_file()), None)
    if build_path is None:
        raise ValueError(f"Cannot detect game version: missing .build.info in {game} or its parent")

    with build_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.reader(stream, delimiter="|")
        columns = [column.split("!", 1)[0] for column in next(rows, [])]
        if len(set(columns)) != len(columns) or not {"Product", "Version", "Active"} <= set(columns):
            raise ValueError(f"Invalid .build.info header in {build_path}")

        versions = set()
        for values in rows:
            if not values:
                continue
            if len(values) != len(columns):
                raise ValueError(f"Invalid .build.info row in {build_path}")

            row = dict(zip(columns, values))
            if row["Product"] == product and row["Active"] == "1":
                versions.add(row["Version"])

    if len(versions) != 1:
        raise ValueError(f"Missing or ambiguous active build for {product} in {build_path}")

    version = versions.pop()
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise ValueError(f"Invalid client version {version!r} in {build_path}")

    major, minor, patch, _ = map(int, match.groups())
    flavor = {
        "wow": "retail",
        "wow_classic": "classic",
        "wow_classic_era": "classic-era",
        "wowf": "forever",
    }.get(product, product)
    # The beta product slot can be reused for other Classic releases.
    if product == "wow_classic_beta" and (major, minor) == (1, 60):
        flavor = "forever"

    return GameCompatibility(
        flavor=flavor,
        interface=major * 10000 + minor * 100 + patch,
    )


def validate_compatibility(game: Path, manifest: Manifest) -> None:
    """Reject incompatible targets, but warn and allow older addon targets."""
    fields = ("flavor", "interface")
    packages = [package for package in manifest.packages
                if package.compatibility is not None
                and any(getattr(package.compatibility, field) is not None for field in fields)]
    if not packages:
        return

    client = detect_client(game)
    for package in packages:
        compatibility = package.compatibility
        if compatibility.flavor is not None and compatibility.flavor != client.flavor:
            raise ValueError(
                f"{package.name}: targets game flavor {compatibility.flavor}, "
                f"but the installed client is {client.flavor}"
            )

        expected = compatibility.interface
        actual = client.interface
        if expected is None or expected == actual:
            continue
        if expected > actual:
            raise ValueError(
                f"{package.name}: targets game interface {expected}, newer than the installed "
                f"client ({actual}); update the game or select an older addon release"
            )

        print(f"warning: {package.name}: out of date "
              f"(game interface: addon targets {expected}, installed client is {actual})",
              file=sys.stderr)
