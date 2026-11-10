{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "spoken";
  version = "3.8.5";

  srcs = [
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/spoken/v3.8.5/Spoken-3.8.5.zip";
      hash = "sha256-k/x3Py+0TEm120sHEotzSWba+DRKwm9RVMQtseXVqBo=";
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
