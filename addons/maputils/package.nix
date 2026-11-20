{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.7.22";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9721/259/MapUtils-v1.7.22-forever.zip";
      hash = "sha256-cDDFMqns1+eFZxkFGpEm38fpqI4DtZEN7Hd6nJPkXXw=";
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
