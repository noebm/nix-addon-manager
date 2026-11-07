{
  lib,
  python3,
  nix,
  makeWrapper,
  stdenvNoCC,
}:

stdenvNoCC.mkDerivation {
  pname = "nix-addon-updater";
  version = "0.1.0";
  src = lib.cleanSourceWith {
    src = ../../updater;
    filter = path: type: lib.cleanSourceFilter path type && baseNameOf path != "__pycache__";
  };
  nativeBuildInputs = [ makeWrapper ];
  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p "$out/lib/nix-addon-manager/updater" "$out/bin"
    cp *.py "$out/lib/nix-addon-manager/updater/"
    makeWrapper ${python3}/bin/python3 "$out/bin/nix-addon-updater" \
      --add-flags "-m updater.main" \
      --prefix PYTHONPATH : "$out/lib/nix-addon-manager" \
      --prefix PATH : ${lib.makeBinPath [ nix ]}

    runHook postInstall
  '';

  meta = {
    description = "Discover and validate pinned World of Warcraft addon updates";
    mainProgram = "nix-addon-updater";
    platforms = lib.platforms.linux;
  };
}
