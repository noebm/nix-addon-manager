{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "1.6.1";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9819/422/ForeverLevelingBiS-v1.6.1-forever.zip";
      hash = "sha256-UyXtp/9ltj9iYRLkHPJw8tFM90w17xL1GlMyLc4q9tc=";
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
