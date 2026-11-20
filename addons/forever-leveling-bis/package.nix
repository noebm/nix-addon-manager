{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "1.4.2";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9709/520/ForeverLevelingBiS-v1.4.2-forever.zip";
      hash = "sha256-TmVjLzmIcUPNJuUKGt8n6x91N5Hly2R70Hwkc3YxoA8=";
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
