{
  lib,
  mkAddonBundle,
  callPackage,
}:

let
  components = map (path: callPackage path { }) [
    ./components/code/package.nix
    ./components/quests-audio/package.nix
    ./components/readables-audio/package.nix
    ./components/places-audio/package.nix
    ./components/bosses-audio/package.nix
  ];
in
mkAddonBundle {
  pname = "spoken-english";
  inherit (builtins.head components) version;
  paths = components;

  meta = {
    description = "Spoken WoW addon with all English voice packs";
    homepage = "https://github.com/rusty-key/spoken-wow";
    license = lib.licenses.unfree;
  };
}
