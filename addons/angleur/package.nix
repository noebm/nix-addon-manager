{
  lib,
  stdenvNoCC,
  fetchurl,
  unzip,
}:

stdenvNoCC.mkDerivation {
  pname = "angleur";
  version = "2.9.8-AutoEquipFishingRod";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9494/10/Angleur-2.9.8-AutoEquipFishingRod.zip";
      hash = "sha256-go22e6wkg+bekvjHQkmv8uSrIDcAISRJT9o5OLrCY8s=";
    })
  ];

  nativeBuildInputs = [ unzip ];
  dontUnpack = true;
  dontBuild = true;

  passthru = {
    addonDirectories = [ "Angleur" ];
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
    description = "One-button fishing and automatic fishing gear for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/angleur";
    license = lib.licenses.unfree;
    platforms = lib.platforms.all;
  };
}
