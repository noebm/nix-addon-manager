{
  lib,
  mkAddonBundle,
  callPackage,
}:

let
  components = lib.mapAttrs (_: path: callPackage path { }) {
    code = ./components/code/package.nix;
    quests-audio = ./components/quests-audio/package.nix;
    readables-audio = ./components/readables-audio/package.nix;
    places-audio = ./components/places-audio/package.nix;
    bosses-audio = ./components/bosses-audio/package.nix;
  };
in
mkAddonBundle {
  pname = "spoken-english";
  inherit (components.code) version;
  paths = builtins.attrValues components;

  meta = {
    description = "Spoken WoW addon with all English voice packs";
    homepage = "https://github.com/rusty-key/spoken-wow";
    license = lib.licenses.unfree;
  };
}
