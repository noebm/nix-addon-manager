{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.7.30";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9764/293/MapUtils-v1.7.30-forever.zip";
      hash = "sha256-YpZnmPEWnY8w2ByWYMDHEvnbkdc79ODMJ+iT839o7G4=";
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
