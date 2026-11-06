# nix-addon-manager

Reproducible Nix packages and a declarative installer for World of Warcraft addons.
Select addons in a Nix configuration, preview the changes, and apply them to a
game installation independently of your host configuration.

## Package structure

- `addons/`: addon packages and fixed bundles.
- `modules/`: configurable addons, with choices such as language or voice packs.
- `pkgs/`: tools, including the installer.

Addon and tool packages are exposed through the flake's `packages` output.
Releases and download hashes are pinned in addon definitions; `flake.lock` pins
nixpkgs.

## Usage

Requires Nix with flakes enabled.

Build an individual package:

```sh
nix build .#<package-name>
```

Create an `addons.nix` configuration selecting your addons:

```nix
{ addons, ... }:
[ addons.<package-name> ]
```

The configuration receives `pkgs`, `lib`, `addons`, and `modules`. It describes
the complete desired selection for one game installation.

Addons are installed under `Interface/AddOns` inside the supplied game path.
Unrelated addons and game settings under `WTF` are left untouched.

Check that your selected addons support your game flavor and version.

Preview changes for a game directory containing `Interface/AddOns`:

```sh
nix run .#installer -- --game-path /path/to/WoW/_classic_ --config ./addons.nix
```

The preview lists these operations:

- **Install:** add a missing selected directory.
- **Update:** replace a managed directory whose selected package changed.
- **Remove:** remove a managed directory no longer selected.
- **Keep:** leave a directory that already matches unchanged.

Apply the selection:

```sh
nix run .#installer -- --game-path /path/to/WoW/_classic_ --config ./addons.nix --apply
```

Recover an interrupted installation:

```sh
nix run .#installer -- --game-path /path/to/WoW/_classic_ --recover
```

## Supported addons

| Addon | Package | Notes |
| --- | --- | --- |
| AtlasLoot Classic Forever | `atlasloot-classic-forever` | BiS tooltips; WoW Forever 1.60.1 (interface 16001) |
| Spoken | `spoken-english` | All English voice packs; unfree audio |
