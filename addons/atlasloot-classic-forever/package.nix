{
  lib,
  stdenvNoCC,
  fetchurl,
  unzip,
}:

stdenvNoCC.mkDerivation {
  pname = "atlasloot-classic-forever";
  version = "1.0.1";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9484/783/AtlasLoot-Classic-Forever-1.3.2-071126-16001.zip";
      hash = "sha256-LDt7NObKSwuJkMoesSNT3zX43A6kx4+v3CRYSBhGAas=";
    })
  ];

  nativeBuildInputs = [ unzip ];
  dontUnpack = true;
  dontBuild = true;

  passthru = {
    addonDirectories = [
      "AtlasBIStooltips"
      "AtlasLootClassic"
      "AtlasLootClassic_Collections"
      "AtlasLootClassic_Crafting"
      "AtlasLootClassic_Data"
      "AtlasLootClassic_DungeonsAndRaids"
      "AtlasLootClassic_Factions"
      "AtlasLootClassic_Options"
      "AtlasLootClassic_PvP"
    ];
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
    description = "AtlasLoot loot tables and best-in-slot lists for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/atlasloot-forever";
    license = lib.licenses.gpl2Only;
    platforms = lib.platforms.all;
  };
}
