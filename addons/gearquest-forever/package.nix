{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "gearquest-forever";
  version = "1.4.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9816/352/GearQuestForever-v1.4.0.zip";
      hash = "sha256-uBh6lTr7UrzWiZ4z+y7cvBs45BSF8Kbm9ENdk7tpZIU=";
    })
  ];

  addonDirectories = [
      "GearQuestForever"
      "GearQuestForever_DRUID"
      "GearQuestForever_HUNTER"
      "GearQuestForever_ItemStats"
      "GearQuestForever_Languages"
      "GearQuestForever_MAGE"
      "GearQuestForever_PALADIN"
      "GearQuestForever_PRIEST"
      "GearQuestForever_ROGUE"
      "GearQuestForever_SHAMAN"
      "GearQuestForever_WARLOCK"
      "GearQuestForever_WARRIOR"
    ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    displayName = "GearQuest Forever";
    description = "Leveling gear upgrades and hunt tracking for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/gearquest-forever";
    license = lib.licenses.unfree;
  };
}
