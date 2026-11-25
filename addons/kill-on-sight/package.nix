{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "kill-on-sight";
  version = "4.0.2";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9816/369/KillOnSight-forever-4.0.2.zip";
      hash = "sha256-J991y0Hi4ZG9qwRdyY2aFrTr8GyZx95/lGc946MAl7c=";
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
