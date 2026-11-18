{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "kill-on-sight";
  version = "3.5.8";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9679/287/KillOnSight-forever-3.5.8.zip";
      hash = "sha256-4URQ6//siLeQGoZPkOqvRoD0B4T9bbGdETktqwhc6S4=";
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
