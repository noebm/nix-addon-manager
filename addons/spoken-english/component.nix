{
  lib,
  stdenvNoCC,
  unzip,
  pname,
  version,
  srcs,
  addonDirectories,
  description,
}:

stdenvNoCC.mkDerivation {
  inherit pname version srcs;
  nativeBuildInputs = [ unzip ];
  dontUnpack = true;
  dontBuild = true;
  passthru = { inherit addonDirectories; };

  installPhase = ''
    runHook preInstall

    mkdir -p "$out/share/wow-addons"
    for archive in $srcs; do
      unzip -q "$archive" -d "$out/share/wow-addons"
    done

    runHook postInstall
  '';

  meta = {
    inherit description;
    homepage = "https://github.com/rusty-key/spoken-wow";
    # Retain the existing classification; game-derived audio is unfree.
    license = lib.licenses.unfree;
    platforms = lib.platforms.all;
  };
}
