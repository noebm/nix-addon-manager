{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.0.4";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9583/985/DungeonJournal-2.0.4.zip";
      hash = "sha256-SUMMJlYLtcgGMV3ZtjPjPQ2GPEEO1eqkkXXPY0tdO8I=";
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
