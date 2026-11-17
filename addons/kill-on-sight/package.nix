{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "kill-on-sight";
  version = "3.5.7";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9643/833/KillOnSight-forever-3.5.7.zip";
      hash = "sha256-20tk1WX0Xgk/gEMygdUsx6kuIzcR1HedwGtSPTJHzVc=";
    })
  ];

  addonDirectories = [ "KillOnSight" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    description = "Hostile player and guild tracking with nearby alerts for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/kill-on-sight";
    license = lib.licenses.mit;
  };
}
