{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "books-on-map-forever";
  version = "2.3.1";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9622/361/Books_on_map_Foreverv2.3.1.zip";
      hash = "sha256-uYvc0U30DRTb4jaQk8I24ZL33hXZnTofPZs+NlTjQOk=";
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
