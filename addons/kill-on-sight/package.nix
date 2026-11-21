{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "kill-on-sight";
  version = "3.6.4";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9729/837/KillOnSight-forever-3.6.4.zip";
      hash = "sha256-KMoGa4zUJuIauRvxLgbwFmvqLd1uV9ptOUDF4PJEcQg=";
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
