# nix-addon-manager

Reproducible Nix packages and a declarative installer for World of Warcraft addons.
Select addons in a Nix configuration, preview the changes, and apply them to a
game installation independently of your host configuration.

The project is still at an early stage; expect some slop.

## Package structure

- `addons/<name>/`: addon packages and fixed bundles.
- `pkgs/<name>/package.nix`: packages for the installer and updater tools.
- `installer/` and `updater/`: Python implementations of those tools.
- `lib/`: shared addon and bundle builders, and manifest evaluation.

Addon and tool packages are exposed through the flake's `packages` output.
Releases and download hashes are pinned in addon and component definitions;
`flake.lock` pins the flake's dependencies.

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

The configuration receives `pkgs`, `lib`, and `addons`. It describes
the complete desired selection for one game installation.

The installer and the flake's package outputs enable `allowUnfree` so addons with
unfree licenses can be built.

Addons are installed under `Interface/AddOns` inside the supplied game path.
Unrelated addons and game settings under `WTF` are left untouched.

The installer checks declared addon compatibility against the installed client.
It rejects mismatched game flavors and addons targeting a newer game interface,
and warns when an addon targets an older interface. These checks require
`.flavor.info` in the game directory and `.build.info` there or in its parent.

Register an installation and select a default:

```sh
nix run .#installer -- installations add /path/to/WoW/_forever_
nix run .#installer -- installations default /path/to/WoW/_forever_
nix run .#installer -- installations list
nix run .#installer -- --config ./addons.nix
```

Omit `--game-path` to use the selected default. `--game-path`,
`installations default`, and `installations remove` accept a directory or a unique installation ID prefix.
IDs display as 4 characters, extended when needed to distinguish installations.
Use `--full` on an installations command (for example, `installations list --full`)
to show complete hashes.
Run `installations default` without an argument to show the current default.
`installations remove <path-or-id>` unregisters a directory without removing its addons.

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

Export the same selection as a compressed ZIP without a game directory:

```sh
nix run .#installer -- --config ./addons.nix --export-zip ./addons.zip
```

The export builds the pinned packages and includes actual files, with addon folders
at the archive root. Extract it into `Interface/AddOns` on the target machine.
No installation state is created. The destination must not already exist;
`--export-zip` cannot be combined with `--game-path`, `--apply`, or `--recover`.

Recover an interrupted installation:

```sh
nix run .#installer -- --game-path /path/to/WoW/_forever_ --recover
```

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
| `roots/<generation-id>` | Nix GC roots keeping manifests and addon generations available. |

Backups and GC roots are retained; automatic pruning is not implemented.

## Supported addons

| Addon | Package | Notes |
| --- | --- | --- |
| Angleur | `angleur` | One-button fishing and automatic fishing gear; WoW Forever 1.60.1 (interface 16001); unfree |
| AtlasLoot Classic Forever | `atlasloot-classic-forever` | BiS tooltips; WoW Forever 1.60.1 (interface 16001) |
| Books on Map Forever | `books-on-map-forever` | Library book tracking; WoW Forever 1.60.1 (interface 16001); unfree |
| Spoken | `spoken-english` | All English voice packs; unfree audio |
| DungeonJournal | `dungeonjournal` | Dungeon boss loot and quests; WoW Forever 1.60.1 (interface 16001); unfree |
| Kill on Sight | `kill-on-sight` | Hostile player and guild tracking with nearby alerts; WoW Forever 1.60.1 (interface 16001) |
| MapUtils | `maputils` | Dungeon maps, travel routes, and world map improvements; WoW Forever 1.60.1 (interface 16001) |

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
