{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.7.29";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9756/503/MapUtils-v1.7.29-forever.zip";
      hash = "sha256-hxZKXfSnW8SkWgCTYCJ4m6U8Z24JRvC5vTZchpZ605I=";
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
