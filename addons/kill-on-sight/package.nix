{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "kill-on-sight";
  version = "3.6.5";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9764/187/KillOnSight-forever-3.6.5.zip";
      hash = "sha256-oLMLwYcYqBCFgBb4dOItdmHClvz7uW7t2BoRGs1Gr6w=";
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
