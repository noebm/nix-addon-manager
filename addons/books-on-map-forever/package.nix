{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "books-on-map-forever";
  version = "2.2.4";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9542/253/Books_on_map_Foreverv2.2.4.zip";
      hash = "sha256-1akb/hjFsV/h91Sn2XG0k7b2rrrp+zIQwbzNSTBPwdA=";
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
