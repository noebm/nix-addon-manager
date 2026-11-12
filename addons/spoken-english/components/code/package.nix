{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "spoken";
  version = "3.8.7";

  srcs = [
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/spoken/v3.8.7/Spoken-3.8.7.zip";
      hash = "sha256-qehgoaQ8kVER4tmamUz6oAWQ3sH7+F4Ib3DHBvVPgNc=";
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
