{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "spoken-places-audio-english";
  version = "2.1.0";

  srcs = [
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/places-audio/v2.1.0/SpokenPlacesAudio-2.1.0.zip";
      hash = "sha256-3GHXRhn0DX+R+iq45UcEakPa2sgtYJXgfdguozUZbks=";
    })
  ];

  addonDirectories = [
    "SpokenPlacesAudio"
  ];

  meta = {
    description = "Spoken English places audio";
    homepage = "https://github.com/rusty-key/spoken-wow";
    license = lib.licenses.unfree;
  };
}
