{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "spoken-bosses-audio-english";
  version = "1.0.0";

  srcs = [
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/bosses-audio/v1.0.0/SpokenBossesAudio-1.0.0.zip";
      hash = "sha256-nQI9kju/eJTQ+S/sAl/5m7+2TLpCuG0WWYdPQi4ecdY=";
    })
  ];

  addonDirectories = [
    "SpokenBossesAudio"
  ];

  meta = {
    description = "Spoken English boss audio";
    homepage = "https://github.com/rusty-key/spoken-wow";
    license = lib.licenses.unfree;
  };
}
