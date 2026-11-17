{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "faster-loot";
  version = "20261117";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9663/533/FasterLoot-20261117.zip";
      hash = "sha256-r8yh4sSsXz4LhHZacKV7BisaoU1pgjQOFW9zScVI6I0=";
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
