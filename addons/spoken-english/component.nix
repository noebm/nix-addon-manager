{
  lib,
  mkAddon,
  pname,
  version,
  srcs,
  addonDirectories,
  description,
}:

mkAddon {
  inherit pname version srcs;
  inherit addonDirectories;

  meta = {
    inherit description;
    homepage = "https://github.com/rusty-key/spoken-wow";
    # Retain the existing classification; game-derived audio is unfree.
    license = lib.licenses.unfree;
  };
}
