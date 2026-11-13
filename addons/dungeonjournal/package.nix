{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.0.5";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9595/820/DungeonJournal-2.0.5.zip";
      hash = "sha256-3o2BBsOBPIe+8SENEBRNJS0yY8Puqoy7/v13dH4mYm4=";
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
