{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "1.4.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9696/63/ForeverLevelingBiS-v1.4.0-forever.zip";
      hash = "sha256-5Ta88vmxBSpOFFda5Qjrq+5fPCUtX0zZEr1a8Giycd0=";
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
