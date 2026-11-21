{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "1.4.4";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9723/943/ForeverLevelingBiS-v1.4.4-forever.zip";
      hash = "sha256-4Z4T54DEVuMrPihKNSdEcUvXv990mm7AcHHq0n/lkV0=";
    })
  ];

  addonDirectories = [ "ForeverLevelingBiS" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    description = "Best-in-slot leveling gear from quests, dungeons and crafting for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/forever-leveling-bis";
    license = lib.licenses.unfree;
  };
}
