{
  lib,
  stdenvNoCC,
  fetchurl,
  libarchive,
}:

stdenvNoCC.mkDerivation {
  pname = "atlasloot-classic-forever";
  version = "1.0.1";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9503/738/AtlasLoot-Classic-Forever-1.3.3-081126-16001.zip";
      hash = "sha256-Hgs5oLUFUWSbBY0EprEYpaCxmClDkBZIrV/kCpvkF84=";
    })
  ];

  nativeBuildInputs = [ libarchive ];
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
      bsdtar -xf "$archive" -s '|\\|/|g' -C "$out/share/wow-addons"
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
