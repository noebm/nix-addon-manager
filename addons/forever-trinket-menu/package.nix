{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-trinket-menu";
  version = "1.8.23";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9826/650/ForeverTrinketMenu-v1.8.23.zip";
      hash = "sha256-t5SjTd+gZfPHxnibWDbmFIyRz4shXiM2i9sZgyrHuPk=";
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
