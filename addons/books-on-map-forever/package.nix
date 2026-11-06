{
  lib,
  stdenvNoCC,
  fetchurl,
  unzip,
}:

stdenvNoCC.mkDerivation {
  pname = "books-on-map-forever";
  version = "2.2.1";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9474/284/Books_on_map_Foreverv2.2.1.zip";
      hash = "sha256-nd3kS4mLqIc4FtNc6sPnzD4DhJ9QFyUQwR3fXq0noSE=";
    })
  ];

  nativeBuildInputs = [ unzip ];
  dontUnpack = true;
  dontBuild = true;

  passthru = {
    addonDirectories = [ "Books_on_map_Forever" ];
    gameCompatibility = {
      flavor = "forever";
      version = "1.60.1";
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
