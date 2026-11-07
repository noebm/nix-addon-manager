{
  callPackage,
  fetchurl,
}:

callPackage ../../component.nix {
  pname = "spoken";
  version = "3.8.3";

  srcs = [
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/spoken/v3.8.3/Spoken-3.8.3.zip";
      hash = "sha256-s8ggNlvT9PMyQIUSC0vE3D0wp38wF+9sacRU+C4QHcc=";
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
