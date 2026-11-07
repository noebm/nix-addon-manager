{
  lib,
  stdenvNoCC,
  fetchurl,
  unzip,
}:

stdenvNoCC.mkDerivation {
  pname = "books-on-map-forever";
  version = "2.2.2";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9488/530/Books_on_map_Foreverv2.2.2.zip";
      hash = "sha256-2UDOZVqmxrW3X+uPO1Fh9XlvYAWRgJD+84U0TpAjcHo=";
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
