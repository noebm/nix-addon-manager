# nix-addon-manager

Nix packages and Home Manager modules for World of Warcraft addon bundles.
Currently provides Spoken with all English voice packs, pinned to GitHub releases.

Build with `nix build .#spoken-english`.

Import `inputs.nix-addon-manager.homeManagerModules.spoken` and configure:

```nix
programs.spoken = {
  enable = true;
  gamePath = "/home/user/Games/World of Warcraft/_forever_";
};
```

The module links individual addon folders into `Interface/AddOns`. Existing
folders must be backed up and moved aside before activation. Other addons and
WTF settings remain outside its ownership. Keep Spoken outside other addon
managers to avoid competing updates.

The package includes game-derived audio outside the code's MIT license and is
marked unfree. The standalone flake allows this package; consuming Home Manager
configurations must allow it in their own nixpkgs configuration.

No imperative installer is implemented yet.

See [AGENTS.md](AGENTS.md) for project direction, the intended bundle model, and
requirements for a possible imperative installer.
