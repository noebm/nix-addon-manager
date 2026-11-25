{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.7.38";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9816/119/MapUtils-v1.7.38-forever.zip";
      hash = "sha256-Gt3e8n9hiZ9rhb9LqqY9yHpHJCmr0qzGyjOVS3WmjEg=";
    })
  ];

  addonDirectories = [ "MapUtils" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    displayName = "MapUtils";
    description = "Dungeon maps, travel routes, and world map improvements for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/maputils";
    license = lib.licenses.gpl3Only;
  };
}
