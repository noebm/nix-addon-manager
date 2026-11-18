{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "gearquest-forever";
  version = "1.2.3";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9682/627/GearQuestForever-v1.2.3.zip";
      hash = "sha256-4qSgwVwKOgqdXq2U4J4w8dVtCMZ1fOo008zvOUxXNyA=";
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
    description = "Leveling gear upgrades and hunt tracking for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/gearquest-forever";
    license = lib.licenses.unfree;
  };
}
