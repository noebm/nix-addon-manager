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

Create an `addons.nix` configuration selecting your addons. For example, to install
Spoken and AtlasLoot Classic Forever together:

```nix
{ addons, ... }:
[
  addons.spoken-english
  addons.atlasloot-classic-forever
]
```

The configuration receives `pkgs`, `lib`, `addons`, and `modules`. It describes
the complete desired selection for one game installation.

Addons are installed under `Interface/AddOns` inside the supplied game path.
Unrelated addons and game settings under `WTF` are left untouched.

Check that your selected addons support your game flavor and version.

Preview changes for a game directory containing `Interface/AddOns`:

```sh
nix run .#installer -- --game-path /path/to/WoW/_forever_ --config ./addons.nix
```

The preview lists these operations:

- **Install:** add a missing selected directory.
- **Update:** replace a managed directory whose selected package changed.
- **Remove:** remove a managed directory no longer selected.
- **Keep:** leave a directory that already matches unchanged.

Apply the selection:

```sh
nix run .#installer -- --game-path /path/to/WoW/_forever_ --config ./addons.nix --apply
```

Recover an interrupted installation:

```sh
nix run .#installer -- --game-path /path/to/WoW/_forever_ --recover
```

## Storage

Addon files and generated manifests live in the Nix store. The game's addon
directory contains links to the addon files. Your `addons.nix` configuration stays
where you saved it.

Other installer files live under
`$XDG_STATE_HOME/nix-addon-manager/<installation-id>/`, defaulting to
`~/.local/state/nix-addon-manager/<installation-id>/`. Each game installation has
its own directory. To change this location, set `XDG_STATE_HOME` to an absolute
path outside the game directory.

| Location within that directory | Contents |
| --- | --- |
| `state.json` | Installed selection and managed directory ownership. |
| `lock` | Lock file preventing concurrent operations. |
| `transaction/` | Pending installation journal, staged links, and recovery links. |
| `backups/<transaction-id>/` | Previous addon links retained after changes. |
| `roots/<generation-id>` | Nix GC roots keeping manifests and addon generations available. |

Backups and GC roots are retained; automatic pruning is not implemented.

## Supported addons

| Addon | Package | Notes |
| --- | --- | --- |
| AtlasLoot Classic Forever | `atlasloot-classic-forever` | BiS tooltips; WoW Forever 1.60.1 (interface 16001) |
| Books on Map Forever | `books-on-map-forever` | Library book tracking; WoW Forever 1.60.1 (interface 16001); unfree |
| Spoken | `spoken-english` | All English voice packs; unfree audio |
| DungeonJournal | `dungeonjournal` | Dungeon boss loot and quests; WoW Forever 1.60.1 (interface 16001); unfree |
