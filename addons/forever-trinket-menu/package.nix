{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "forever-trinket-menu";
  version = "1.8.19";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9778/147/ForeverTrinketMenu-v1.8.19.zip";
      hash = "sha256-MVKxAFt6Y8/0J/Mzv45uzr+OP5cy/2MnBMSYfkjEU34=";
    })
  ];

  addonDirectories = [ "ForeverTrinketMenu" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    description = "Quick trinket swapping, combat queue and auto-rotation for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/forever-trinket-menu";
    license = lib.licenses.mit;
  };
}
