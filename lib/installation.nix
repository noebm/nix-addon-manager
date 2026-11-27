{
  config,
  options,
  lib,
  pkgs,
  addons,
  installationFile,
  ...
}:
let
  types = import ./types.nix { inherit lib; };

  definition = import (builtins.toPath installationFile) {
    inherit
      config
      options
      lib
      pkgs
      addons
      ;
  };
  # MIGRATION (manifest schema 1 -> 2): remove this adapter and its test
  # when list-only configuration guidance is retired.
  userModule =
    if builtins.isList definition then
      throw ''
        List-only addon configurations are no longer supported (${installationFile}).
        Put your existing addon list and game path under installation:

        { addons, ... }: {
          installation.gamePath = "/path/to/WoW/_forever_";
          installation.addons = [
            # Your existing addons go here.
          ];
        }

        Update commands now use installation.gamePath from this file; remove --game-path from them.
      ''
    else
      definition // { _file = installationFile; };
in
{
  imports = [ userModule ];

  options.installation = {
    gamePath = lib.mkOption {
      type = lib.types.nonEmptyStr;
      description = "Game directory, expressed as a quoted string rather than a Nix path.";
    };
    addons = lib.mkOption {
      type = lib.types.listOf types.addonOrBundle;
      default = throw "The option `installation.addons' must be defined, even if it is an empty list.";
      description = "Selected addon packages.";
    };
  };
}
