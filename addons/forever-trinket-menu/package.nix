{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-trinket-menu";
  version = "1.8.22";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9818/330/ForeverTrinketMenu-v1.8.22.zip";
      hash = "sha256-o04Go5kAQh7da97F++LRcnGegTMCx2VMjXhiKKGzTbs=";
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
