{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "angleur";
  version = "Angleur Forever Angleur-2.9.82-ToggleEquipmentColdFix";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9753/318/Angleur-Angleur-2.9.82-ToggleEquipmentColdFix.zip";
      hash = "sha256-WXCyQX1LLwN9SY99+dJ78Zqd2cczaSbKyv3LxS9x6lg=";
    })
  ];

  addonDirectories = [ "Angleur" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    description = "One-button fishing and automatic fishing gear for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/angleur";
    license = lib.licenses.unfree;
  };
}
