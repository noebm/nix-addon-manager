{
  repository,
  configuration,
  build ? true,
}:
let
  flake = builtins.getFlake repository;
  pkgs = import flake.inputs.nixpkgs {
    system = builtins.currentSystem;
    config.allowUnfree = true;
  };
  packages = import (builtins.toPath configuration) {
    inherit pkgs;
    inherit (pkgs) lib;
    addons = import ../addons { inherit pkgs; };
    modules = flake.addonModules;
  };
  manifest = {
    schema = 1;
    packages = map (package: {
      name = package.pname;
      inherit (package) version;
      path = toString package;
      directories = package.addonDirectories;
      compatibility = package.gameCompatibility or null;
      sources = map (source: {
        inherit (source) url;
        hash = source.outputHash;
        hashAlgorithm = source.outputHashAlgo;
      }) (package.srcs or [ ]);
    }) (pkgs.lib.concatMap (package: package.paths or [ package ]) packages);
  };
in
if build then pkgs.writeText "addon-manifest.json" (builtins.toJSON manifest) else manifest
