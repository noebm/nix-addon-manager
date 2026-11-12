{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "books-on-map-forever";
  version = "2.2.5";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9567/645/Books_on_map_Foreverv2.2.5.zip";
      hash = "sha256-F9PRs4Vyg44e2LlCmizh006ZLvV5jy+vzxXQndLTp8I=";
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
