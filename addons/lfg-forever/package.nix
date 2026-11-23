{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "lfg-forever";
  version = "2.5.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9747/838/LFGForever.zip";
      hash = "sha256-WHI6bE2tI0Oni3DYHesgW12yt7mftC5HxkpwPqMGb+c=";
    })
  ];

  addonDirectories = [ "LFGForever" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    description = "Dungeon group finder with role, class and level filters for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/lfg-forever";
    license = lib.licenses.gpl3Only;
  };
}
