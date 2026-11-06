{ pkgs }:

{
  atlasloot-classic-forever = pkgs.callPackage ./atlasloot-classic-forever/package.nix { };
  books-on-map-forever = pkgs.callPackage ./books-on-map-forever/package.nix { };
  spoken-english = pkgs.callPackage ./spoken-english/package.nix { };
}
