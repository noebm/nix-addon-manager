{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "1.3.3";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9671/768/ForeverLevelingBiS-v1.3.3-forever.zip";
      hash = "sha256-M/GhXg0mxNFEv/Pl8Pi4Uju1IiGhY8wl4fnwRwWlugo=";
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
