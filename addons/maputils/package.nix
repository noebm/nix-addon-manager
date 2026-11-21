{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.7.23";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9725/180/MapUtils-v1.7.23-forever.zip";
      hash = "sha256-TSZocDK9N0RVZmsLJOepDOzTv23MSsOWsvtZHrzxV90=";
    })
  ];

  addonDirectories = [ "MapUtils" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    description = "Dungeon maps, travel routes, and world map improvements for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/maputils";
    license = lib.licenses.gpl3Only;
  };
}
