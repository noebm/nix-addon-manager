{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-trinket-menu";
  version = "1.8.21";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9809/11/ForeverTrinketMenu-v1.8.21.zip";
      hash = "sha256-dZstS1uyr3pdZp+cDmhHfYJfwONe2H2vecfA8uELBfM=";
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
