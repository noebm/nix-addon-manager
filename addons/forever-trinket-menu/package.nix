{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-trinket-menu";
  version = "1.8.20";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9800/850/ForeverTrinketMenu-v1.8.20.zip";
      hash = "sha256-cUEYgYuxC/I5Dg9afZyMGQyifrAPv/0fMXuUD5v1IwM=";
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
