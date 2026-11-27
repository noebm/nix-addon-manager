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
    doInstallCheck = true;

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

    installCheckPhase = ''
      runHook preInstallCheck

      for directory in ${lib.escapeShellArgs addonDirectories}; do
        addon="$out/share/wow-addons/$directory"
        if [ ! -d "$addon" ]; then
          echo "Addon directory $directory is missing; expected a directory containing a .toc file" >&2
          exit 1
        fi

        foundToc=false
        for toc in "$addon"/*.toc; do
          if [ -f "$toc" ]; then
            foundToc=true
            break
          fi
        done

        if [ "$foundToc" = false ]; then
          echo "Addon directory $directory contains no .toc file" >&2
          exit 1
        fi
      done

      ${args.installCheckPhase or ""}

      runHook postInstallCheck
    '';

    meta = {
      platforms = lib.platforms.all;
    }
    // meta;
  }
)
