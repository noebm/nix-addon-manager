{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "dungeonjournal";
  version = "2.1.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9705/465/DungeonJournal2.1.0.zip";
      hash = "sha256-VrIrM5LlkR1F/JueeZQNc7NkOXUPkiSjhGrlVVwzruc=";
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
