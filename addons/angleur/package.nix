{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "angleur";
  version = "2.9.8-AutoEquipFishingRod";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9494/10/Angleur-2.9.8-AutoEquipFishingRod.zip";
      hash = "sha256-go22e6wkg+bekvjHQkmv8uSrIDcAISRJT9o5OLrCY8s=";
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
