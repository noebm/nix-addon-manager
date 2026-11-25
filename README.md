# nix-addon-manager

Reproducible Nix packages and a declarative installer for World of Warcraft addons.
Select addons in a Nix configuration, preview the changes, and apply them to a
game installation independently of your host configuration.

The project is still at an early stage; expect some slop.

## Usage

> [!NOTE]
> Requires Nix with flakes enabled.

Run the commands in this section with `nix run github:noebm/nix-addon-manager --`
(or explicitly `nix run github:noebm/nix-addon-manager#installer --`), followed by
the command and its arguments.

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

> [!TIP]
> If expected updates are not found, add `--refresh` before the `--` separator
> to refresh Nix's cache: `nix run --refresh github:noebm/nix-addon-manager -- update ...`.

Replace `/path/to/WoW/_forever_` with the game directory containing
`Interface/AddOns` and `.flavor.info`, with `.build.info` there or in its parent.
Omit `--apply` to [preview the changes](#updating-addons) first.
You can also [register a default installation](#installation-management) to omit `--game-path`.

### Updating addons

The configuration receives `addons`, `pkgs`, and `lib`; unfree addons are enabled.
The installer leaves unrelated addons and `WTF` settings untouched. It rejects
mismatched game flavors and newer addon interfaces, and warns about older ones.

Edit `addons.nix` and use these commands to preview, apply, or export your selection:

| Arguments | Action |
| --- | --- |
| `update ./addons.nix [--apply]` | Preview the changes and use `--apply` to apply them. |
| `export ./addons.nix --output ./addons.zip` | Export the selected addons as a ZIP archive. |

Add `--game-path <path-or-id>` to an update command to select an installation,
or use the default.

Addon versions are pinned in this repository and updated by its maintainers.
Rerun the command to install the versions currently pinned in the repository.

For ZIP exports, extract the archive into `Interface/AddOns` on the target machine. The ZIP
must not already exist. Export creates no installation state.

### Installation management

| Arguments | Action |
| --- | --- |
| `installations add <path>` | Register a game installation. |
| `installations list` | List registered installations. |
| `installations default [<path-or-id>]` | Set the default installation with `<path-or-id>`, or omit it to show the default. |
| `installations remove <path-or-id>` | Unregister an installation without removing addons. |
| `recover` | Recover an interrupted installation without a configuration. |

`--game-path`, `installations default`, and `installations remove` accept a path
or unique ID prefix. Use `--full` on an installations command to show full IDs.
Add `--game-path <path-or-id>` to `recover` to select an installation,
or omit it to use the default.

### Generation management

Each update saves a generation of your installation. **Previous generations are
not removed automatically.** After you remove them, Nix can free the space they
used the next time garbage collection runs.

Manage retained generations with these commands.

| Arguments | Action |
| --- | --- |
| `generations list` | List saved generations. |
| `generations remove <id>` | Remove an inactive generation by ID or unique prefix. |
| `generations prune` | Remove all inactive generations. |

Generation commands operate on all saved installations, including unregistered
installations and games whose directories no longer exist. Add
`--game-path <path-or-id>` after the generation subcommand to limit it to one
installation; an unregistered installation can still be selected by its old path.
Generation ID prefixes must be unique across the selected installations.
Pruning preserves each installation's recorded current generation.

## Supported addons

List all addons with their exported name (for use as `addons.<name>` in
`addons.nix`), display name, pinned version, description, and homepage:

```sh
nix eval --json github:noebm/nix-addon-manager#addonList
```

In a local checkout, use `nix eval --json .#addonList`.

| Addon | Package | Notes |
| --- | --- | --- |
| Angleur | `angleur` | One-button fishing and automatic fishing gear; WoW Forever 1.60.1 (interface 16001); unfree |
| AtlasLoot Classic Forever | `atlasloot-classic-forever` | BiS tooltips; WoW Forever 1.60.1 (interface 16001) |
| Books on Map Forever | `books-on-map-forever` | Library book tracking; WoW Forever 1.60.1 (interface 16001); unfree |
| Spoken | `spoken-english` | All English voice packs; unfree audio |
| DungeonJournal | `dungeonjournal` | Dungeon boss loot and quests; WoW Forever 1.60.1 (interface 16001); unfree |
| Faster Loot | `faster-loot` | Instant looting of mobs and containers; WoW Forever 1.60.1 (interface 16001); unfree |
| Forever Leveling BiS | `forever-leveling-bis` | Best-in-slot leveling gear from quests, dungeons and crafting; WoW Forever 1.60.1 (interface 16001); unfree |
| Forever Trinket Menu | `forever-trinket-menu` | Quick trinket swapping, combat queue and auto-rotation; WoW Forever 1.60.1 (interface 16001) |
| GearQuest Forever | `gearquest-forever` | Leveling gear upgrades and hunt tracking; WoW Forever 1.60.1 (interface 16001); unfree |
| Kill on Sight | `kill-on-sight` | Hostile player and guild tracking with nearby alerts; WoW Forever 1.60.1 (interface 16001) |
| LFG Forever | `lfg-forever` | Dungeon group finder with role, class and level filters; WoW Forever 1.60.1 (interface 16001) |
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
