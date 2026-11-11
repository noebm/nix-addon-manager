{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.6.1";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9558/587/MapUtils-v1.6.1-forever.zip";
      hash = "sha256-WIxTBOKn4w1D7pbaMkSE/Ro8jm9katmGh+7FvUw2VoU=";
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
