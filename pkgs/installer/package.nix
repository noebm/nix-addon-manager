{
  lib,
  python3,
  nix,
  makeWrapper,
  stdenvNoCC,
}:

stdenvNoCC.mkDerivation {
  pname = "nix-addon-manager";
  version = "0.1.0";
  src = lib.cleanSourceWith {
    src = ../..;
    filter = path: type: lib.cleanSourceFilter path type && baseNameOf path != "__pycache__";
  };
  nativeBuildInputs = [ makeWrapper ];
  dontBuild = true;
  doCheck = true;
  nativeCheckInputs = [ python3 ];

  checkPhase = ''
    runHook preCheck

    # Manifest evaluation needs Nix store access outside the build sandbox.
    PYTHONPATH="$PWD:$PWD/tests" python -m unittest test_installer test_installations test_generations

    runHook postCheck
  '';

  installPhase = ''
    runHook preInstall

    mkdir -p "$out/lib/nix-addon-manager" "$out/bin"
    cp -r installer lib pkgs addons flake.nix flake.lock "$out/lib/nix-addon-manager/"
    makeWrapper ${python3}/bin/python3 "$out/bin/nix-addon-manager" \
      --add-flags "-m installer.main" \
      --prefix PYTHONPATH : "$out/lib/nix-addon-manager" \
      --prefix PATH : ${lib.makeBinPath [ nix ]}

    runHook postInstall
  '';

  meta = {
    description = "Install declaratively selected World of Warcraft addons";
    mainProgram = "nix-addon-manager";
    platforms = lib.platforms.linux;
  };
}
