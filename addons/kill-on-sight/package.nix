{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "kill-on-sight";
  version = "3.6.3";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9727/911/KillOnSight-forever-3.6.3.zip";
      hash = "sha256-7vXgxrdzi30+4WWsEIr5PMTB6zGX0sqWg97EWhtsFeI=";
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
