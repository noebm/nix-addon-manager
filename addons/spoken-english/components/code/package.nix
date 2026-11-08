{
  callPackage,
  fetchurl,
}:

callPackage ../../component.nix {
  pname = "spoken";
  version = "3.8.4";

  srcs = [
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/spoken/v3.8.4/Spoken-3.8.4.zip";
      hash = "sha256-dGGS6+Gp3irTTRnIWIT5FhUyvztr1AC7eM2ttHj/PI0=";
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
