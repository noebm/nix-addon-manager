{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "angleur";
  version = "Angleur Forever 2.9.81-EqManAndLuaErrorHotfixes";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9554/931/Angleur-2.9.81-EqManAndLuaErrorHotfixes.zip";
      hash = "sha256-6mW7FvvUZcc/YHANhvK6kj+bXWhqTBaviL2EvO8mHrE=";
    })
  ];

  addonDirectories = [ "Angleur" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    description = "One-button fishing and automatic fishing gear for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/angleur";
    license = lib.licenses.unfree;
  };
}
