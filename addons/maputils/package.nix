{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.7.25";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9744/111/MapUtils-v1.7.25-forever.zip";
      hash = "sha256-/B7gX1PaMruNdl3UaakGtrOIlUBjN3QrHbIwJFsMCoQ=";
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
