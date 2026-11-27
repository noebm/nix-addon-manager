{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "kill-on-sight";
  version = "4.0.4";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9823/387/KillOnSight-forever-4.0.4.zip";
      hash = "sha256-wJ4OONzCNEIfe871lmzYUqDi0KEB/qSVqNnUTX07QBs=";
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
