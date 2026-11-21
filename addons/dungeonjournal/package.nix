{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.1.2";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9730/326/DungeonJournal2.1.2.zip";
      hash = "sha256-Yn3Xg4ychbpAncYzKNSoaT+qvgGbUib36KmvZhpQq8Q=";
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
