{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "1.4.1";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9704/404/ForeverLevelingBiS-v1.4.1-forever.zip";
      hash = "sha256-TyfvYNNdRsyEz/2pb7lG75aXNCcweic0QU5Uiec3zhU=";
    })
  ];

  addonDirectories = [ "ForeverLevelingBiS" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    description = "Best-in-slot leveling gear from quests, dungeons and crafting for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/forever-leveling-bis";
    license = lib.licenses.unfree;
  };
}
