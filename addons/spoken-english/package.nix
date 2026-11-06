{
  lib,
  stdenvNoCC,
  fetchurl,
  unzip,
}:

stdenvNoCC.mkDerivation {
  pname = "spoken-english";
  version = "3.8.0";

  # Audio has independent release versions and is distributed outside Git.
  srcs = [
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/spoken/v3.8.0/Spoken-3.8.0.zip";
      hash = "sha256-HR1MlO1cIMgqp0fe8ADGSAMp7rOrCsukq8q66Z2CGrs=";
    })
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/quests-audio/v2.5.0/SpokenQuestsAudioAll-2.5.0.zip";
      hash = "sha256-u+cCtx8A+MNYa2/Rx9dLpnWBRJUTtVhiff3JeHsOt5A=";
    })
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/readables-audio/v2.3.0/SpokenReadablesAudio-2.3.0.zip";
      hash = "sha256-fvjWgaVLizbDCWdjeV1F7IXwht8RNacGaPn+dpW+u/o=";
    })
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/places-audio/v2.1.0/SpokenPlacesAudio-2.1.0.zip";
      hash = "sha256-3GHXRhn0DX+R+iq45UcEakPa2sgtYJXgfdguozUZbks=";
    })
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/bosses-audio/v1.0.0/SpokenBossesAudio-1.0.0.zip";
      hash = "sha256-nQI9kju/eJTQ+S/sAl/5m7+2TLpCuG0WWYdPQi4ecdY=";
    })
  ];

  nativeBuildInputs = [ unzip ];
  dontUnpack = true;
  dontBuild = true;

  passthru.addonDirectories = [
    "Spoken"
    "SpokenContributions"
    "Spoken_Bosses"
    "Spoken_Places"
    "Spoken_Quests"
    "Spoken_Readables"
    "SpokenQuestsAudioAlliance"
    "SpokenQuestsAudioHorde"
    "SpokenQuestsAudioShared"
    "SpokenQuestsAudioGossip"
    "SpokenReadablesAudio"
    "SpokenPlacesAudio"
    "SpokenBossesAudio"
  ];

  installPhase = ''
    runHook preInstall

    mkdir -p "$out/share/wow-addons"
    for archive in $srcs; do
      unzip -q "$archive" -d "$out/share/wow-addons"
    done

    runHook postInstall
  '';

  meta = {
    description = "Spoken WoW addon with all English voice packs";
    homepage = "https://github.com/rusty-key/spoken-wow";
    # Audio includes Blizzard-derived material outside the code's MIT grant.
    license = lib.licenses.unfree;
    platforms = lib.platforms.all;
  };
}
