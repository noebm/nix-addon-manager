{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "1.7.1";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9859/818/ForeverLevelingBiS-v1.7.1-forever.zip";
      hash = "sha256-mdbK2N7AVq+uT5LAZ8B0S6ejzX6ShNhRxdUZsoQ51+c=";
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
