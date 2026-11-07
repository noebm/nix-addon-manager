{
  callPackage,
  fetchurl,
}:

callPackage ../../component.nix {
  pname = "spoken";
  version = "3.8.0";

  srcs = [
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/spoken/v3.8.0/Spoken-3.8.0.zip";
      hash = "sha256-HR1MlO1cIMgqp0fe8ADGSAMp7rOrCsukq8q66Z2CGrs=";
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

  description = "Spoken WoW addon code";
}
