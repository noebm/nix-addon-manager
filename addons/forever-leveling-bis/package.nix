{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "1.3.5";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9687/774/ForeverLevelingBiS-v1.3.5-forever.zip";
      hash = "sha256-734/583UrGsWd/LvczMMgXe9P3uBTxr0OpqybZlpJWA=";
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
