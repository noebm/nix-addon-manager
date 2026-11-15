{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.0.8";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9635/381/DungeonJournal-2.0.8.zip";
      hash = "sha256-+JQa2IaHz4fyf5ZQ/1N5HnAtJjG1R/wOgOB8NY7Gi9M=";
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
