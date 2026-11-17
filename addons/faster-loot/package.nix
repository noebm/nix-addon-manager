{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "faster-loot";
  version = "20261016";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9657/496/FasterLoot-20261116-3.zip";
      hash = "sha256-2tOA3H8CMcmjfOc5f+5lK4btCpKlPiD9zcAnS2QWG8I=";
    })
  ];

  addonDirectories = [ "FasterLoot" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    description = "Instant looting of mobs and containers for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/faster-loot";
    license = lib.licenses.unfree;
  };
}
