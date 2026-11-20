{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "gearquest-forever";
  version = "1.2.5";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9708/529/GearQuestForever-v1.2.5.zip";
      hash = "sha256-Hy2lmfZARAG50+MukxAxk81x9xawKUfCysRSw71q3JE=";
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
