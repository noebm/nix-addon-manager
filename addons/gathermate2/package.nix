{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "gathermate2";
  version = "1.52.7";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9600/843/GatherMate2-1.52.7.zip";
      hash = "sha256-54dOhpnTvzoSyrlorT7OxB61+Z+IM/EwXwUWESYD98U=";
    })
  ];

  addonDirectories = [
    "GatherMate2"
    "GatherMate2Storage_Dragonflight"
    "GatherMate2Storage_TheWarWithin"
    "GatherMate2Storage_Midnight"
  ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };
  passthru.versionToc = "GatherMate2/GatherMate2.toc";

  meta = {
    displayName = "GatherMate2";
    description = "Gathering node tracking on the world map and minimap for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/gathermate2";
    license = lib.licenses.unfree;
  };
}
