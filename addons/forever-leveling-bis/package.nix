{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "1.4.5";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9744/210/ForeverLevelingBiS-v1.4.5-forever.zip";
      hash = "sha256-j289BPW50vYLGVnwAeK89LUIC9PTifqnmKkaGX9/UNM=";
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
