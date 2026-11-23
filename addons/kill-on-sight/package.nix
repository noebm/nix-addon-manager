{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "kill-on-sight";
  version = "4.0.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9772/356/KillOnSight-forever-4.0.0.zip";
      hash = "sha256-ExE/VDVSP6+mLQbJ7dPS7AFQ6Zv/JXjcB/s9tKBk6cQ=";
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
