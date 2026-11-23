{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.7.31";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9782/705/MapUtils-v1.7.31-forever.zip";
      hash = "sha256-Ak1t2nTpwiRW1xBWQCBXJJTHHs3+fKHO0WZen2/+qh8=";
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
