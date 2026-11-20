{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "kill-on-sight";
  version = "3.6.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9713/249/KillOnSight-forever-3.6.0.zip";
      hash = "sha256-cvSYQ0AimXCA4B4NcUe0w1v6WQnsCkGHCjcpwv2K0Zg=";
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
