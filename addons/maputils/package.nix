{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.7.11";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9688/22/MapUtils-v1.7.11-forever.zip";
      hash = "sha256-Y4k2GdeSqouSNWVFnCTb7NBlSTiC04pZt/IvQa5k9Ao=";
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
