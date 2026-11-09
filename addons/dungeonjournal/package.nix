{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9532/329/DungeonJournal-2.0.zip";
      hash = "sha256-z2X8lTlOj2Qk3cbHIdmX/MZ1YUEbdY2Znotfid/7m3o=";
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
