{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.7.33";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9784/10/MapUtils-v1.7.33-forever.zip";
      hash = "sha256-6glBvOH/o9TFBiBfbqaZaCdJRMJOKTaML3asZ3B168g=";
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
