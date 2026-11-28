{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-trinket-menu";
  version = "1.9.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9862/821/ForeverTrinketMenu-v1.9.0.zip";
      hash = "sha256-ghy/KrjD440V5Bspp2eCTTH790G/j+tTP0PLJOtU8+w=";
    })
  ];

  addonDirectories = [ "ForeverTrinketMenu" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    displayName = "Forever Trinket Menu";
    description = "Quick trinket swapping, combat queue and auto-rotation for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/forever-trinket-menu";
    license = lib.licenses.mit;
  };
}
