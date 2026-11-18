{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.0.11";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9678/417/DungeonJournal2.0.11.zip";
      hash = "sha256-jKPU3xo7j2dEqV1cym4kMpH+VziEaXUAWzCQJ97Sh+g=";
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
