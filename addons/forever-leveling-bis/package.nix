{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "v1.3.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9616/564/ForeverLevelingBiS-v1.3.0-forever.zip";
      hash = "sha256-Xrdi0N/yW5C0cbvajKzBw9+6KSyYOYLCnH8bAt+OyiI=";
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
