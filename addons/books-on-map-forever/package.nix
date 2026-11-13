{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "books-on-map-forever";
  version = "2.3.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9584/980/Books_on_map_Foreverv2.3.0.zip";
      hash = "sha256-Z54+sq3zlHVf6+xZgiWZrGPpPz6VoRKfdJiiV2QDBdA=";
    })
  ];

  addonDirectories = [ "Books_on_map_Forever" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    description = "Library book locations and collection tracking for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/books-on-map-forever";
    license = lib.licenses.unfree;
  };
}
