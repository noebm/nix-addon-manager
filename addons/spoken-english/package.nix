{
  lib,
  stdenvNoCC,
  callPackage,
}:

let
  components = map (path: callPackage path { }) [
    ./components/code/package.nix
    ./components/quests-audio/package.nix
    ./components/readables-audio/package.nix
    ./components/places-audio/package.nix
    ./components/bosses-audio/package.nix
  ];
in
stdenvNoCC.mkDerivation {
  pname = "spoken-english";
  inherit (builtins.head components) version;
  dontUnpack = true;
  dontBuild = true;

  passthru = {
    addonComponents = components;
    addonDirectories = lib.concatMap (component: component.addonDirectories) components;
    srcs = lib.concatMap (component: component.srcs) components;
  };

  installPhase = ''
    runHook preInstall

    mkdir -p "$out/share/wow-addons"
    ${lib.concatMapStringsSep "\n" (component: ''
      cp -r ${component}/share/wow-addons/. "$out/share/wow-addons/"
    '') components}

    runHook postInstall
  '';

  meta = {
    description = "Spoken WoW addon with all English voice packs";
    homepage = "https://github.com/rusty-key/spoken-wow";
    license = lib.licenses.unfree;
    platforms = lib.platforms.all;
  };
}
