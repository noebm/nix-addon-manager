{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "kill-on-sight";
  version = "4.0.1";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9784/839/KillOnSight-forever-4.0.1.zip";
      hash = "sha256-i2DGpre5lXOGCJs8+X8orNqOObOYtSq1XS5Y9o7kh9A=";
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
