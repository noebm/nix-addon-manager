{
  lib,
  mkAddon,
  fetchurl,
  libarchive,
}:

mkAddon {
  pname = "atlasloot-classic-forever";
  version = "1.5.3";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9861/90/AtlasLoot-Classic-Forever-1.5.3-281126-16001.zip";
      hash = "sha256-Alk4PO70h5Nt/CsN7DP2dLAq7Mdi5rD4YffwFKmCvn8=";
    })
  ];

  passthru.versionToc = "AtlasLootClassic/AtlasLootClassic.toc";

  nativeBuildInputs = [ libarchive ];

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
    interface = 16001;
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
    displayName = "AtlasLoot Classic Forever";
    description = "AtlasLoot loot tables and best-in-slot lists for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/atlasloot-forever";
    license = lib.licenses.gpl2Only;
  };
}
