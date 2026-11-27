{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "1.7.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9848/119/ForeverLevelingBiS-v1.7.0-forever.zip";
      hash = "sha256-3EP0X5+UplXcX76D4CVJpiJ0EWSKP7B9UjPmCm50WFw=";
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
