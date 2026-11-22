{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "books-on-map-forever";
  version = "2.3.3";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9741/390/Books_on_map_Foreverv2.3.3.zip";
      hash = "sha256-FUKxrx6a1FqNG/QX90TC6cetRyAs/EMdpK3pUDAmc2c=";
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
