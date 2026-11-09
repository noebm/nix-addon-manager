{
  lib,
  buildEnv,
}:

{
  paths,
  passthru ? { },
  meta ? { },
  ...
}@args:
buildEnv (
  args
  // {
    pathsToLink = [ "/share/wow-addons" ];

    passthru = passthru // {
      addonDirectories = lib.concatMap (package: package.addonDirectories) paths;
      srcs = lib.concatMap (package: package.srcs or [ ]) paths;
    };

    meta = {
      platforms = lib.platforms.all;
    }
    // meta;
  }
)
