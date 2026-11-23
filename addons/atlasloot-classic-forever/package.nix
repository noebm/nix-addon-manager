{
  lib,
  mkAddon,
  fetchurl,
  libarchive,
}:

mkAddon {
  pname = "atlasloot-classic-forever";
  version = "1.4.8";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9763/940/AtlasLoot-Classic-Forever-1.4.8-231126-16001.zip";
      hash = "sha256-DwMFSONh/0y4F5ETFx3bKMSiAqDnAMh6pOYsr7Rfmj8=";
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
    description = "AtlasLoot loot tables and best-in-slot lists for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/atlasloot-forever";
    license = lib.licenses.gpl2Only;
  };
}
