{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "kill-on-sight";
  version = "3.5.9";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9694/639/KillOnSight-forever-3.5.9.zip";
      hash = "sha256-5iCSsSkek0TvMA/Lmj1K/PPEQ/p1cf26+1hCpRUUjGg=";
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
