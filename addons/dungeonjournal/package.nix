{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.1.4";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9771/279/DungeonJournal2.1.4.zip";
      hash = "sha256-r05f0Ek96ZAXXOktU0bquRH+E18WjDgoEwPq+VAqIb8=";
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
