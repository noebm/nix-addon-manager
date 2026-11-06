{ pkgs }:

{
  installer = pkgs.callPackage ./installer/package.nix { };
}
