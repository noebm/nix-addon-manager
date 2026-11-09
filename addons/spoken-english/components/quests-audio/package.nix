{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "spoken-quests-audio-english";
  version = "2.5.0";

  srcs = [
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/quests-audio/v2.5.0/SpokenQuestsAudioAll-2.5.0.zip";
      hash = "sha256-u+cCtx8A+MNYa2/Rx9dLpnWBRJUTtVhiff3JeHsOt5A=";
    })
  ];

  addonDirectories = [
    "SpokenQuestsAudioAlliance"
    "SpokenQuestsAudioHorde"
    "SpokenQuestsAudioShared"
    "SpokenQuestsAudioGossip"
  ];

  meta = {
    description = "Spoken English quest audio";
    homepage = "https://github.com/rusty-key/spoken-wow";
    license = lib.licenses.unfree;
  };
}
