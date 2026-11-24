{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "1.5.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9794/334/ForeverLevelingBiS-v1.5.0-forever.zip";
      hash = "sha256-kyPI6WQYhfzguCBIZFCffLwEKmIDuGWhZ7IzxOnf7fk=";
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
