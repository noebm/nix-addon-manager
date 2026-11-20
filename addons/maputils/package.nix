{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.7.16";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9708/403/MapUtils-v1.7.16-forever.zip";
      hash = "sha256-Nf1X33rTQpv+TKkGL8ZIPAVrHN2kARQgaW/3cnF5gAo=";
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
