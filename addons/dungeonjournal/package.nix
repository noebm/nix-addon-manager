{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.1.1";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9723/634/DungeonJournal2.1.1.zip";
      hash = "sha256-OInqSIOlLCsoa+6lKjdWJ7o/3+o9LyvhwUigmSdlIi0=";
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
