{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "kill-on-sight";
  version = "4.0.3";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9817/427/KillOnSight-forever-4.0.3.zip";
      hash = "sha256-80e0a1zpU5AAyoWSSraTwo55hZR4j79T1n/1hfRR1lU=";
    })
  ];

  addonDirectories = [ "KillOnSight" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    displayName = "Kill on Sight";
    description = "Hostile player and guild tracking with nearby alerts for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/kill-on-sight";
    license = lib.licenses.mit;
  };
}
