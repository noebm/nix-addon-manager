{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.7.15";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9703/128/MapUtils-v1.7.15-forever.zip";
      hash = "sha256-aS3+SK55KLhVHuxdfsewOUAa57t25JYYpKdCtiCe+h0=";
    })
  ];

  addonDirectories = [ "MapUtils" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    description = "Dungeon maps, travel routes, and world map improvements for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/maputils";
    license = lib.licenses.gpl3Only;
  };
}
