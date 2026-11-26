{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-leveling-bis";
  version = "1.6.2";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9828/211/ForeverLevelingBiS-v1.6.2-forever.zip";
      hash = "sha256-Ax2oTv09CIvtsf2qie9pkOhxmpw5JlZb/aCaTg5xfH8=";
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
