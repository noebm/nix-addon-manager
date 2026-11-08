{
  lib,
  stdenvNoCC,
  unzip,
}:

# Release archives contain addon directories at their root.
{
  addonDirectories,
  gameCompatibility ? null,
  passthru ? { },
  meta ? { },
  ...
}@args:
stdenvNoCC.mkDerivation (
  (builtins.removeAttrs args [
    "addonDirectories"
    "gameCompatibility"
  ])
  // {
    nativeBuildInputs = args.nativeBuildInputs or [ unzip ];
    dontUnpack = true;
    dontBuild = true;

    passthru =
      passthru
      // {
        inherit addonDirectories;
      }
      // lib.optionalAttrs (gameCompatibility != null) { inherit gameCompatibility; };

    installPhase =
      args.installPhase or ''
        runHook preInstall

        mkdir -p "$out/share/wow-addons"
        for archive in $srcs; do
          unzip -q "$archive" -d "$out/share/wow-addons"
        done

        runHook postInstall
      '';

    meta = {
      platforms = lib.platforms.all;
    }
    // meta;
  }
)
