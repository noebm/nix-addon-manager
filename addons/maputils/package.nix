{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.9.1";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9861/842/MapUtils-v1.9.1-forever.zip";
      hash = "sha256-Ujna4l7z7CQ2rQ7WsWna07mgOjLZcL4EPIRF3sLXSVc=";
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
