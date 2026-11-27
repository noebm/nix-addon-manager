{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.8.2";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9838/568/MapUtils-v1.8.2-forever.zip";
      hash = "sha256-XgiCgWofBk7cd6cFAkxI9B6Eq/IVpCGocJWYLEpw7p8=";
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
