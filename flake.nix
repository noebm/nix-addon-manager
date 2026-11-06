{
  description = "Declarative World of Warcraft addon bundles";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };
    in
    {
      packages.${system} = (import ./pkgs { inherit pkgs; }) // (import ./addons { inherit pkgs; });
      addonModules.spoken = ./modules/spoken.nix;
      formatter.${system} = pkgs.nixfmt-tree;
    };
}
