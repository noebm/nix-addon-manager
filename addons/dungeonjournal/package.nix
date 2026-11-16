{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.0.9";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9650/596/DungeonJournal2.0.9.zip";
      hash = "sha256-A6eHorFkZb6lvwKDVNADIi/dDSXsbBgbBwF6rSpBAFo=";
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
