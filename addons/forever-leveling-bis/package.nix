{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "1.3.4";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9678/909/ForeverLevelingBiS-v1.3.4-forever.zip";
      hash = "sha256-7EvQ3GdSOtiM5o9aq31YkA0I7ahkCBbhoN7hSRC926g=";
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
