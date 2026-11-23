{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "1.4.7";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9768/255/ForeverLevelingBiS-v1.4.7-forever.zip";
      hash = "sha256-tPSMxRwAqM8WoH7PPMJ8HYlxzLu9/+bMk85xTacDZ5E=";
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
