{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.1.3";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9741/988/DungeonJournal2.1.3.zip";
      hash = "sha256-rJEqtosTxvkPU3IT37zljPKXGWoguTxXCOstBHA7c1U=";
    })
  ];

  addonDirectories = [ "ForeverDungeonJournal" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    description = "Dungeon boss loot and quest journal for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/dungeonjournal";
    license = lib.licenses.unfree;
  };
}
