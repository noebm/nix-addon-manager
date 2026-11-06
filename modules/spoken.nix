{
  config,
  lib,
  pkgs,
  ...
}:

{
  options.spoken = {
    language = lib.mkOption {
      type = lib.types.enum [ "en" ];
      default = "en";
      description = "Spoken audio language. Currently only English is packaged.";
    };
    package = lib.mkOption {
      type = lib.types.package;
      readOnly = true;
      description = "Spoken package selected by the language configuration.";
    };
  };

  config.spoken.package =
    let
      addons = import ../addons { inherit pkgs; };
      languages = {
        en = addons.spoken-english;
      };
    in
    languages.${config.spoken.language};
}
