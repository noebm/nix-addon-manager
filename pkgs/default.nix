{ pkgs }:

{
  updater = pkgs.callPackage ./updater/package.nix { };
  installer = pkgs.callPackage ./installer/package.nix { };
}
