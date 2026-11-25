{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "lfg-forever";
  version = "2.7.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9804/804/LFGForever.zip";
      hash = "sha256-8ZhnamSN1g6yqcKyKSoY5FSK4hh/peDF/gIl0GW14ck=";
    })
  ];

  addonDirectories = [ "LFGForever" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    displayName = "LFG Forever";
    description = "Dungeon group finder with role, class and level filters for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/lfg-forever";
    license = lib.licenses.gpl3Only;
  };
}
