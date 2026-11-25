{
  repository,
  installationFile,
  build ? true,
}:
let
  flake = builtins.getFlake repository;
  pkgs = import flake.inputs.nixpkgs {
    system = builtins.currentSystem;
    config.allowUnfree = true;
  };
  inherit (pkgs) lib;
  installation =
    (lib.evalModules {
      specialArgs = {
        inherit pkgs installationFile;
        addons = import ../addons { inherit pkgs; };
      };
      modules = [ ./installation.nix ];
    }).config;
  manifest = {
    schema = 2;
    gamePath = installation.gamePath;
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
    }) (pkgs.lib.concatMap (package: package.paths or [ package ]) installation.addons);
  };
in
if build then pkgs.writeText "addon-manifest.json" (builtins.toJSON manifest) else manifest
