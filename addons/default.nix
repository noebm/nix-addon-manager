{ pkgs }:

let
  scope = pkgs.lib.makeScope pkgs.newScope (self: {
    mkAddon = self.callPackage ../lib/mk-addon.nix { };
    mkAddonBundle = self.callPackage ../lib/mk-addon-bundle.nix { };

    angleur = self.callPackage ./angleur/package.nix { };
    atlasloot-classic-forever = self.callPackage ./atlasloot-classic-forever/package.nix { };
    books-on-map-forever = self.callPackage ./books-on-map-forever/package.nix { };
    dungeonjournal = self.callPackage ./dungeonjournal/package.nix { };
    kill-on-sight = self.callPackage ./kill-on-sight/package.nix { };
    maputils = self.callPackage ./maputils/package.nix { };
    spoken-english = self.callPackage ./spoken-english/package.nix { };
  });
in
{
  inherit (scope)
    angleur
    atlasloot-classic-forever
    books-on-map-forever
    dungeonjournal
    kill-on-sight
    maputils
    spoken-english
    ;
}
