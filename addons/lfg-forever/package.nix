{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "lfg-forever";
  version = "2.9.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9855/797/LFGForever.zip";
      hash = "sha256-n7ibYpJC6NVn5uGn4nMPcPJgxtRUwQFnPFycIRbV5j0=";
    })
  ];

  addonDirectories = [ "LFGForever" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    displayName = "LFG Forever";
    description = "Dungeon group finder with role, class and level filters for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/lfg-forever";
    license = lib.licenses.gpl3Only;
  };
}
