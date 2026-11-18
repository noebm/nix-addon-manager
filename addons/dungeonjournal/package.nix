{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.0.12";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9687/205/DungeonJournal2.0.12.zip";
      hash = "sha256-yYX6q+UTgwylcz5X86jzXHQY15v1vl9jdH1nN1A6B9M=";
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
