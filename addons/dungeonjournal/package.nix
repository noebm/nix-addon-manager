{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.0.2";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9557/612/DungeonJournal-2.0.2.zip";
      hash = "sha256-9pTq2RKgeanp2tCJnzfydPlkb49rJrGoX8+Tjwueagk=";
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
