# Changelog

## 0.6.0

- **Breaking change:** Remove the `generations list`, `generations remove`, and `generations prune`
  commands. Applied updates and recovery now release inactive GC roots while
  preserving the installed generation. Previous builds remain reusable until
  Nix garbage collection removes them.

  Existing roots are cleaned on the next `update --apply`, even when no addons
  change. Run the global cleanup command to release inactive roots across all
  saved installations, including all roots for deleted games:

  ```sh
  nix run github:noebm/nix-addon-manager -- cleanup
  ```

  Cleanup preserves current roots for existing games and skips busy installations
  and interrupted transactions. Recover interrupted transactions and rerun cleanup
  to release their unused roots. Run Nix garbage collection to reclaim the space.

## 0.5.0

- Group configuration options under `installation`: use `installation.gamePath`
  and `installation.addons`. Discovery prints the namespaced game path.
  List-only configuration errors show how to migrate directly to this layout.

  Migrate by putting your existing addon list in `installation.addons`, adding
  `installation.gamePath`, and removing `--game-path` from update commands:

  ```nix
  { addons, ... }:
  {
    installation = {
      gamePath = "/path/to/WoW/_forever_";
      addons = [
        addons.spoken-english
        addons.atlasloot-classic-forever
      ];
    };
  }
  ```

  ```sh
  nix run github:noebm/nix-addon-manager -- update ./addons.nix --apply
  ```

## 0.4.0

- **Breaking change:** Recovery accepts `recover <config-or-game-directory>`
  instead of `recover --game-path <path>`. Configuration files supply `gamePath`;
  game directories allow recovery without Nix evaluation.

## 0.3.0

- **Breaking change:** Remove manual installation registration, the
  `installations` commands, default installation selection, and installation ID
  shortcuts. Updates use `gamePath` from `addons.nix`; recovery now requires
  `recover --game-path <path>`. Generation commands continue to discover all
  saved installations automatically; use `--game-path <path>` to filter them
  instead of an installation ID. Existing per-installation state and generations
  remain available.

## 0.2.0

- **Breaking change:** Declare each installation in `addons.nix` as a Nix module
  with required `gamePath` (a nonempty quoted string) and `addons` (a list of
  packages) options. This replaces configurations returning only an addon list
  and makes `update` use the configured game path instead of `--game-path` or the
  registered default installation. Module imports and option merging are
  supported, configuration options are validated, and manifest schema 2 carries
  the game path. Old configurations and `update --game-path` produce migration
  guidance. ZIP exports use the same configuration format but ignore `gamePath`.

  Migrate by wrapping your existing addon list in the `addons` attribute, adding
  `gamePath`, and removing `--game-path` from update commands:

  ```nix
  { addons, ... }:
  {
    gamePath = "/path/to/WoW/_forever_";
    addons = [
      addons.spoken-english
      addons.atlasloot-classic-forever
    ];
  }
  ```

  ```sh
  nix run github:noebm/nix-addon-manager -- update ./addons.nix --apply
  ```
