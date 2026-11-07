{
  callPackage,
  fetchurl,
}:

callPackage ../../component.nix {
  pname = "spoken-readables-audio-english";
  version = "2.3.0";

  srcs = [
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/readables-audio/v2.3.0/SpokenReadablesAudio-2.3.0.zip";
      hash = "sha256-fvjWgaVLizbDCWdjeV1F7IXwht8RNacGaPn+dpW+u/o=";
    })
  ];

  addonDirectories = [
    "SpokenReadablesAudio"
  ];

  description = "Spoken English readables audio";
}
