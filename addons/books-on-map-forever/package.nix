{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "books-on-map-forever";
  version = "2.3.2";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9688/789/Books_on_map_Foreverv2.3.2.zip";
      hash = "sha256-feFmB4maVZ+dsQQwof3aQh23vM2Sy9NY7SyUWwCUP4M=";
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
