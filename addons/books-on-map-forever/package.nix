{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "books-on-map-forever";
  version = "2.4.1";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9820/222/Books_on_map_Foreverv2.4.1.zip";
      hash = "sha256-WII25uXLXoyXRRPV+8lULLe7Z62A5XoXLR5D9VCLVMM=";
    })
  ];

  addonDirectories = [ "Books_on_map_Forever" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    displayName = "Books on Map Forever";
    description = "Library book locations and collection tracking for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/books-on-map-forever";
    license = lib.licenses.unfree;
  };
}
