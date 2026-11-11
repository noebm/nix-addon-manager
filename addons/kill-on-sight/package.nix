{
  lib,
  mkAddon,
  fetchurl,
}:

mkAddon {
  pname = "kill-on-sight";
  version = "3.5.0";

  srcs = [
    (fetchurl {
      url = "https://edge.forgecdn.net/files/9546/933/KillOnSight-forever-3.5.0.zip";
      hash = "sha256-WQns3/0JkAuV7ij8gGwO9cS1DZu9Iq8ZOs/pzLYXJC8=";
    })
  ];

  addonDirectories = [ "KillOnSight" ];
  gameCompatibility = {
    flavor = "forever";
    interface = 16001;
  };

  meta = {
    description = "Hostile player and guild tracking with nearby alerts for WoW Forever";
    homepage = "https://www.curseforge.com/wow/addons/kill-on-sight";
    license = lib.licenses.mit;
  };
}
