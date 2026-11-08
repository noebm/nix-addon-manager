{ pkgs }:

let
  scope = pkgs.lib.makeScope pkgs.newScope (self: {
    mkAddon = self.callPackage ../lib/mk-addon.nix { };

    angleur = self.callPackage ./angleur/package.nix { };
    atlasloot-classic-forever = self.callPackage ./atlasloot-classic-forever/package.nix { };
    books-on-map-forever = self.callPackage ./books-on-map-forever/package.nix { };
    dungeonjournal = self.callPackage ./dungeonjournal/package.nix { };
    spoken-english = self.callPackage ./spoken-english/package.nix { };
  });
in
{
  inherit (scope)
    angleur
    atlasloot-classic-forever
    books-on-map-forever
    dungeonjournal
    spoken-english
    ;
}
