{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "spoken";
  version = "3.12.1";

  srcs = [
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/spoken/v3.12.1/Spoken-3.12.1.zip";
      hash = "sha256-9PIbL2S7fI5/L5LQGs31zlTYy3aOffrvyKQiY3c1KEI=";
    })
  ];

  addonDirectories = [
    "Spoken"
    "SpokenContributions"
    "Spoken_Bosses"
    "Spoken_Places"
    "Spoken_Quests"
    "Spoken_Readables"
  ];

  meta = {
    description = "Spoken WoW addon code";
    homepage = "https://github.com/rusty-key/spoken-wow";
    license = lib.licenses.unfree;
  };
}
