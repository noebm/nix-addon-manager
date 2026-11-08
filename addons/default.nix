{ pkgs }:

{
  angleur = pkgs.callPackage ./angleur/package.nix { };
  atlasloot-classic-forever = pkgs.callPackage ./atlasloot-classic-forever/package.nix { };
  books-on-map-forever = pkgs.callPackage ./books-on-map-forever/package.nix { };
  dungeonjournal = pkgs.callPackage ./dungeonjournal/package.nix { };
  spoken-english = pkgs.callPackage ./spoken-english/package.nix { };
}
