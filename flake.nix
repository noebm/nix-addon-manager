{
  description = "Declarative World of Warcraft addon bundles";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.git-hooks = {
    url = "github:cachix/git-hooks.nix";
    inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    { nixpkgs, git-hooks, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };
      packages = import ./pkgs { inherit pkgs; };
      pre-commit-check = git-hooks.lib.${system}.run {
        src = ./.;
        excludes = [ "^tests/" ];
        hooks.ruff.enable = true;
        hooks.ruff-format.enable = true;
      };
    in
    {
      packages.${system} = packages // (import ./addons { inherit pkgs; });
      formatter.${system} = pkgs.nixfmt-tree;
      checks.${system} = {
        inherit pre-commit-check;
        inherit (packages) installer updater;
      };
      devShells.${system}.default = pkgs.mkShell {
        inherit (pre-commit-check) shellHook;
        packages = [ pkgs.python3 ] ++ pre-commit-check.enabledPackages;
      };
    };
}
