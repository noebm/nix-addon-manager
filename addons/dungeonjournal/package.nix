{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.0.10";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9669/30/DungeonJournal2.0.10.zip";
      hash = "sha256-hdMguQBTtyyNsiWERiVpZROryiVPtplMjBy0NBLCl/w=";
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
