{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "books-on-map-forever";
  version = "2.4.3";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9829/989/Books_on_map_Foreverv2.4.3.zip";
      hash = "sha256-UdHjlfIw96Xy9M+wex9F8WsP/3DpfmnWepSjAO4xVMQ=";
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
