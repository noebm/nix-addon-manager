{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.1.6";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9808/872/DungeonJournal2.1.6.zip";
      hash = "sha256-ZIYAK7OK0r5hR3rRF91ARFxfAiInY6TqQuqIdChzk7M=";
    })
  ];

  addonDirectories = [ "ForeverDungeonJournal" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    displayName = "DungeonJournal";
    description = "Dungeon boss loot and quest journal for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/dungeonjournal";
    license = lib.licenses.unfree;
  };
}
