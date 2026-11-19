{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.7.12";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9692/68/MapUtils-v1.7.12-forever.zip";
      hash = "sha256-LKkhlw4XgIpngDVBo4mF3I5OoU0Gdya7WKe0Z7VsraU=";
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
