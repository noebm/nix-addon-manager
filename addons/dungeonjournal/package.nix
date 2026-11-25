{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.1.5";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9788/295/DungeonJournal2.1.5.zip";
      hash = "sha256-6L9k+7mgOaZPvZ0ITRvcin7zGsLYUbkdRBC+EthA8K0=";
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
