{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.7.39";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9820/970/MapUtils-v1.7.39-forever.zip";
      hash = "sha256-X36H/fzhxGkzQgaeWEPtFzbIiQ//WcPNSvmd0nUlnHQ=";
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
