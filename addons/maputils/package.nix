{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.7.7";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9650/165/MapUtils-v1.7.7-forever.zip";
      hash = "sha256-PYVpys+4/n8ain4Pvlb2aENKaSdfJz4NaWA0MevzxSY=";
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
