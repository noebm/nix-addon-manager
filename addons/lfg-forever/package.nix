{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "lfg-forever";
  version = "2.8.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9817/410/LFGForever.zip";
      hash = "sha256-gdK+KJUuHkWbDJi62teiY1Wv9asF0oJLp+u3N0cjuhQ=";
    })
  ];

  addonDirectories = [ "LFGForever" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    displayName = "LFG Forever";
    description = "Dungeon group finder with role, class and level filters for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/lfg-forever";
    license = lib.licenses.gpl3Only;
  };
}
