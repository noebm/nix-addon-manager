{
  lib,
  stdenvNoCC,
  fetchurl,
  unzip,
}:

stdenvNoCC.mkDerivation {
  pname = "dungeonjournal";
  version = "1.7.3";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9506/720/ForeverDungeonJournal-1.7.3.zip";
      hash = "sha256-8Pg6oVPTSSw30EUpp3oMMviWA2riLmP5/LeZaBRhAj4=";
    })
  ];

  nativeBuildInputs = [ unzip ];
  dontUnpack = true;
  dontBuild = true;

  passthru = {
    addonDirectories = [ "ForeverDungeonJournal" ];
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
    description = "Dungeon boss loot and quest journal for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/dungeonjournal";
    license = lib.licenses.unfree;
    platforms = lib.platforms.all;
  };
}
