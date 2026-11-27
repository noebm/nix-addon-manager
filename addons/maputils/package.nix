{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.8.4";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9851/952/MapUtils-v1.8.4-forever.zip";
      hash = "sha256-wzVpZprwBqC6hwMHN5ywa+TsnMlHn5BNJpSHCuXhWSs=";
    })
  ];

  addonDirectories = [ "MapUtils" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    displayName = "MapUtils";
    description = "Dungeon maps, travel routes, and world map improvements for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/maputils";
    license = lib.licenses.gpl3Only;
  };
}
