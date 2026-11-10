{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.0.1";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9547/760/ForeverDungeonJournal-2.0.1.zip";
      hash = "sha256-8EV+kSafufIEnQX30/N/WO8mWslS2owYRQ8CJzsMRbs=";
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
