{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "spoken";
  version = "3.11.0";

  srcs = [
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/spoken/v3.11.0/Spoken-3.11.0.zip";
      hash = "sha256-qKamkx6KVZe8lCYJZ3V6jdwB43d9kDzR2mtrutY4dxc=";
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
