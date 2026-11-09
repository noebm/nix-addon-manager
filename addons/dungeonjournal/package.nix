{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "1.7.4";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9518/674/ForeverDungeonJournal-1.7.4.zip";
      hash = "sha256-TCSReq4ypJXQ2rrlUehmFWNbpKN+ypNLjdWZqTQ5qDs=";
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
