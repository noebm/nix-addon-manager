{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.0.7";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9620/47/DungeonJournal-2.0.7.zip";
      hash = "sha256-sMswiw+jG/oW/oTtpl2e61D3zo+DT18kkzApZMvFl+s=";
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
