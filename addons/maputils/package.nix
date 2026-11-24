{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "maputils";
  version = "1.7.35";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9799/275/MapUtils-v1.7.35-forever.zip";
      hash = "sha256-yt9cz8DOjsBcC+aqUBSwFaXkESJVIfQGp1ncclr9pwc=";
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
