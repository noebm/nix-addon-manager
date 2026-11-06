# nix-addon-manager

Nix packages and configurable modules for World of Warcraft addons.

Tool packages live under `pkgs/`; addon packages live under `addons/`. Both
collections are exposed through the flake's standard `packages` output.

Build Spoken with `nix build .#spoken-english`.

Ordinary addons and fixed bundles use packages. Modules are for configuration
choices such as language or optional voice packs. The Spoken module is available
as `addonModules.spoken`; only English (`en`) is currently packaged.

Packages expose `pname`, `version`, `addonDirectories`, and their addon content
under `share/wow-addons`. Consumers decide how to install that content.

Releases and hashes are pinned in addon package definitions; `flake.lock` pins
nixpkgs. Spoken includes game-derived audio outside the code's MIT license and is
marked unfree. Consumers must allow it in their nixpkgs configuration.

## Supported addons

| Addon | Package | Notes |
| --- | --- | --- |
| Spoken | `spoken-english` | All English voice packs; unfree audio |
