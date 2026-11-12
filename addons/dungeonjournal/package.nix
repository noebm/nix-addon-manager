{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.0.3";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9567/829/DungeonJournal-2.0.3.zip";
      hash = "sha256-JL41T6ilhcwlj57+jRsTUA9TK0GBatTUccwpxnZeKjA=";
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
