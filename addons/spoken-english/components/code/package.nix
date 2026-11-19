{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "spoken";
  version = "3.10.1";

  srcs = [
    (fetchurl {
      url = "https://github.com/rusty-key/spoken-wow/releases/download/spoken/v3.10.1/Spoken-3.10.1.zip";
      hash = "sha256-S5nirE95u/1FFcCnwJp4wFxspWDMVYAOxxB/U8mv4AE=";
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
