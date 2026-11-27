{ lib }:
let
  addonPackage = (lib.types.addCheck lib.types.package (package:
    !(package ? paths)
    && lib.types.nonEmptyStr.check (package.pname or null)
    && lib.types.nonEmptyStr.check (package.version or null)
    && builtins.isList (package.addonDirectories or null)
    && builtins.all lib.types.nonEmptyStr.check package.addonDirectories
  )) // {
    name = "addon package";
    description = "addon package";
  };
  addonBundle = (lib.types.addCheck lib.types.package (package:
    builtins.isList (package.paths or null)
    && builtins.all addonPackage.check package.paths
  )) // {
    name = "addon bundle";
    description = "addon bundle";
  };
  addonOrBundle = lib.types.either addonPackage addonBundle;
in
{
  inherit addonPackage addonBundle addonOrBundle;
}
