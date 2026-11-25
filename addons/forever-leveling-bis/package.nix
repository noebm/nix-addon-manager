{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "1.6.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9811/820/ForeverLevelingBiS-v1.6.0-forever.zip";
      hash = "sha256-LhzxwFLgvXUNw12zrUlKB+UH/Hpk8/pKefB0xVRRZFA=";
    })
  ];

  addonDirectories = [ "ForeverLevelingBiS" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    displayName = "Forever Leveling BiS";
    description = "Best-in-slot leveling gear from quests, dungeons and crafting for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/forever-leveling-bis";
    license = lib.licenses.unfree;
  };
}
