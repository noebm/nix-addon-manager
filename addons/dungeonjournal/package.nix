{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.0.6";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9614/11/DungeonJournal-2.0.6.zip";
      hash = "sha256-lyJrj6wumECJd3EWnJUsIlaQwaFlG1Hl+d0FpWV3jxg=";
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
