{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "lfg-forever";
  version = "2.6.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9784/989/LFGForever.zip";
      hash = "sha256-aFKazOLemUdiJlIiQtqs2dJ3/+zVsaiy2cEsmf6+am4=";
    })
  ];

  addonDirectories = [ "LFGForever" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    description = "Dungeon group finder with role, class and level filters for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/lfg-forever";
    license = lib.licenses.gpl3Only;
  };
}
