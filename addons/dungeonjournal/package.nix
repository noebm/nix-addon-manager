{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.1.7";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9825/398/DungeonJournal2.1.7.zip";
      hash = "sha256-wnTQqA+2qAU4odGjwVOVzJkstE7T0xC86CDjIkL+Ta0=";
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
