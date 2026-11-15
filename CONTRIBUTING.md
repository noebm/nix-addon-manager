# Contributing

## Addon packages

Each addon has an `addons/<slug>/package.nix` definition, an export in
`addons/default.nix`, and an entry in the supported addons table in `README.md`.

Packages use `mkAddon` with the following data:

| Field | Value |
| --- | --- |
| `pname` | Package slug. |
| `version` | Release version from the archive TOC. |
| `srcs` | Downloads pinned by exact URL and SHA-256 SRI hash. |
| `addonDirectories` | Every shipped addon directory, including bundled modules. |
| `gameCompatibility.flavor` | `"forever"` for WoW Forever. |
| `gameCompatibility.interface` | Interface version from the archive TOCs. |
| `meta.description` | Brief description of the addon. |
| `meta.homepage` | Canonical upstream project URL. |
| `meta.license` | Upstream license; `lib.licenses.unfree` for All Rights Reserved. |

CurseForge packages use direct CDN URLs and canonical project homepages for updater
compatibility. API discovery belongs in the updater, outside package builds.
`passthru.versionToc` identifies the main TOC when bundled addons have independent
versions. AtlasLoot demonstrates extraction for archives with backslash paths.

## Validation

`nix build path:.#<slug> --no-link` builds a package, including untracked files.
The installed directories should match the declaration, and `git diff --check`
should pass. Addon commits follow the style `addons: add <slug>`.

This guide should stay in sync with the packaging workflow.
