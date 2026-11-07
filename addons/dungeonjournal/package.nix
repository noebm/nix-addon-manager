{
  lib,
  stdenvNoCC,
  fetchurl,
  unzip,
}:

stdenvNoCC.mkDerivation {
  pname = "dungeonjournal";
  version = "1.7.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9473/650/ForeverDungeonJournal-1.7.0.zip";
      hash = "sha256-DQMDQl3aKr4q7qNAeWc931HBdPyL52RujI7KNh8SnJo=";
    })
  ];

  nativeBuildInputs = [ unzip ];
  dontUnpack = true;
  dontBuild = true;

  passthru = {
    addonDirectories = [ "ForeverDungeonJournal" ];
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
    description = "Dungeon boss loot and quest journal for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/dungeonjournal";
    license = lib.licenses.unfree;
    platforms = lib.platforms.all;
  };
}
