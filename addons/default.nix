{ pkgs }:

{
  atlasloot-classic-forever = pkgs.callPackage ./atlasloot-classic-forever/package.nix { };
  spoken-english = pkgs.callPackage ./spoken-english/package.nix { };
}
