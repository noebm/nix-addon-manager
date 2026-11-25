# Changelog

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
