# nix-addon-manager

Reproducible Nix packages and a declarative installer for World of Warcraft addons.
Select addons in a Nix configuration, preview the changes, and apply them to a
game installation independently of your host configuration.

The project is still at an early stage; expect some slop.

## Usage

> [!NOTE]
> Requires Nix with flakes enabled.

### TLDR

Save your [addon selection](#updating-addons) as `addons.nix`, for example:

```nix
{ addons, ... }:
[
  addons.spoken-english
  addons.atlasloot-classic-forever
]
```

Apply it to your game installation:

```sh
nix run github:noebm/nix-addon-manager -- update ./addons.nix --game-path /path/to/WoW/_forever_ --apply
```

Replace `/path/to/WoW/_forever_` with the game directory containing
`Interface/AddOns` and `.flavor.info`, with `.build.info` there or in its parent.
Omit `--apply` to [preview the changes](#updating-addons) first.
You can also [register a default installation](#installation-management) to omit `--game-path`.

### Updating addons

The configuration receives `addons`, `pkgs`, and `lib`; unfree addons are enabled.
The installer leaves unrelated addons and `WTF` settings untouched. It rejects
mismatched game flavors and newer addon interfaces, and warns about older ones.

Edit `addons.nix` and rerun the [command](#tldr). Without `--apply`, the preview shows
which addon directories will be installed, updated, removed, or kept.
Addon versions are pinned in this repository and updated by its maintainers.
Rerun the command to install the versions currently pinned in the repository.

For ZIP export, use the `export` command:

```sh
nix run github:noebm/nix-addon-manager -- export ./addons.nix --output ./addons.zip
```

Extract the archive into `Interface/AddOns` on the target machine. The ZIP
must not already exist. Export creates no installation state.

### Installation management

Register an installation and select a default:

```sh
nix run github:noebm/nix-addon-manager -- installations add /path/to/WoW/_forever_
nix run github:noebm/nix-addon-manager -- installations default /path/to/WoW/_forever_
nix run github:noebm/nix-addon-manager -- installations list
```

Omit `--game-path` to use the default. `--game-path`, `installations default`, and
`installations remove` accept a path or unique ID prefix. Use `--full` on an
installations command to show full IDs. `installations default` without an argument
shows the default; `installations remove <path-or-id>` unregisters it without
removing addons.

If an installation is interrupted, use `recover` to recover it:

```sh
nix run github:noebm/nix-addon-manager -- recover --game-path /path/to/WoW/_forever_
```

Omit `--game-path` to use the default installation. Recovery does not require
a configuration.

### Generation management

Generations retain previous installation states. Use
`nix run github:noebm/nix-addon-manager --` followed by these arguments.
Add `--game-path <path-or-id>` after the generation subcommand to select an
installation, or use the default.

| Arguments | Action |
| --- | --- |
| `generations list` | List retained generations. |
| `generations remove <id>` | Remove an inactive generation by ID or unique prefix. |
| `generations prune` | Remove all inactive generation roots. |

Recover interrupted transactions with [`recover`](#installation-management) before pruning. Removing roots
allows Nix garbage collection to reclaim their store paths; it does not run
garbage collection.

## Supported addons

| Addon | Package | Notes |
| --- | --- | --- |
| Angleur | `angleur` | One-button fishing and automatic fishing gear; WoW Forever 1.60.1 (interface 16001); unfree |
| AtlasLoot Classic Forever | `atlasloot-classic-forever` | BiS tooltips; WoW Forever 1.60.1 (interface 16001) |
| Books on Map Forever | `books-on-map-forever` | Library book tracking; WoW Forever 1.60.1 (interface 16001); unfree |
| Spoken | `spoken-english` | All English voice packs; unfree audio |
| DungeonJournal | `dungeonjournal` | Dungeon boss loot and quests; WoW Forever 1.60.1 (interface 16001); unfree |
| Faster Loot | `faster-loot` | Instant looting of mobs and containers; WoW Forever 1.60.1 (interface 16001); unfree |
| GearQuest Forever | `gearquest-forever` | Leveling gear upgrades and hunt tracking; WoW Forever 1.60.1 (interface 16001); unfree |
| Kill on Sight | `kill-on-sight` | Hostile player and guild tracking with nearby alerts; WoW Forever 1.60.1 (interface 16001) |
| MapUtils | `maputils` | Dungeon maps, travel routes, and world map improvements; WoW Forever 1.60.1 (interface 16001) |

## Package structure

- `addons/<name>/`: addon packages and fixed bundles.
- `pkgs/<name>/package.nix`: packages for the installer and updater tools.
- `installer/` and `updater/`: Python implementations of those tools.
- `lib/`: shared addon and bundle builders, and manifest evaluation.

Addon and tool packages are exposed through the flake's `packages` output.
Releases and download hashes are pinned in addon and component definitions;
`flake.lock` pins the flake's dependencies.

## Storage

Addon files and generated manifests live in the Nix store. The game's addon
directory contains links to the addon files. Your `addons.nix` configuration stays
where you saved it.

Registrations and the default selection are saved in
`$XDG_STATE_HOME/nix-addon-manager/installations.json`, defaulting to
`~/.local/state/nix-addon-manager/installations.json`.

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
| `roots/<generation-id>` | Generation links (Nix GC roots) keeping manifests and addons available. |

Backups and generations are retained; automatic pruning is not implemented.
The storage directory remains named `roots/` for compatibility.

## Updating releases

The updater checks for new stable releases and updates pinned versions and hashes.
Packages with independently versioned bundled addons can set
`passthru.versionToc` to the archive path of their main addon TOC. AtlasLoot uses
this to read its own version instead of the bundled BiS tooltips version.

Set `CURSEFORGE_API_KEY` for CurseForge addons. Spoken needs no key;
`GITHUB_TOKEN` is optional for authenticated GitHub requests.

Preview updates in a writable checkout:

```sh
nix run .#updater
```

Build and validate updates, then write the pins:

```sh
nix run .#updater -- --apply
```

Use `--addon <package-name>` to select one addon.

### GitHub Actions

The `Update addons` workflow builds and validates updates,
then commits changed pins directly to the default branch.

Add `CURSEFORGE_API_KEY` as a repository Actions secret and allow the workflow's
`GITHUB_TOKEN` to push to the default branch.
