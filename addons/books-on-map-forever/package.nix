{
  lib,
  stdenvNoCC,
  fetchurl,
  unzip,
}:

stdenvNoCC.mkDerivation {
  pname = "books-on-map-forever";
  version = "2.2.3";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9500/18/Books_on_map_Foreverv2.2.3.zip";
      hash = "sha256-QiZTimpsXCGgY/xUeHiXGzEGOf6iPRyLvYBy8hnXb30=";
    })
  ];

  nativeBuildInputs = [ unzip ];
  dontUnpack = true;
  dontBuild = true;

  passthru = {
    addonDirectories = [ "Books_on_map_Forever" ];
    gameCompatibility = {
      flavor = "forever";
      interface = 16001;
    };
  };

  installPhase = ''
    runHook preInstall

    mkdir -p "$out/share/wow-addons"
    for archive in $srcs; do
      unzip -q "$archive" -d "$out/share/wow-addons"
    done

    runHook postInstall
  '';

  meta = {
    description = "Library book locations and collection tracking for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/books-on-map-forever";
    license = lib.licenses.unfree;
    platforms = lib.platforms.all;
  };
}
