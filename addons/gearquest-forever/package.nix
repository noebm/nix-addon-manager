{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "gearquest-forever";
  version = "1.4.1";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9829/704/GearQuestForever-v1.4.1.zip";
      hash = "sha256-OZN0JrPrsCSl2lo4q+gS8q/wJAx9HF85Hs7aKFCMicw=";
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
