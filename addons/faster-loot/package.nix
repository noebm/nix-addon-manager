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
      url = "https://edge.forgecdn.net/files/9205/801/FasterLoot.zip";
      hash = "sha256-v8rRFEXRxK3wjpbMp9zqYLefic8UhJYbzFnuRtzmbhU=";
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
