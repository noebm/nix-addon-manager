{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "1.7.3";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9506/720/ForeverDungeonJournal-1.7.3.zip";
      hash = "sha256-8Pg6oVPTSSw30EUpp3oMMviWA2riLmP5/LeZaBRhAj4=";
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
