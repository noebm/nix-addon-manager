{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "1.3.2";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9653/539/ForeverLevelingBiS-v1.3.2-forever.zip";
      hash = "sha256-os4wWPiwN52NdQ9STjLrJjKKqzOMKM/osABRDJvtlFA=";
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
