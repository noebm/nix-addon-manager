# Contributing

## Addon packages

Each addon has an `addons/<slug>/package.nix` definition, an export in
`addons/default.nix`, and an entry in the supported addons table in `README.md`.

Archive packages use `mkAddon` with the following data:

| Field | Value |
| --- | --- |
| `pname` | Package slug. |
| `version` | Release version from the archive TOC. |
| `srcs` | Downloads pinned by exact URL and SHA-256 SRI hash. |
| `addonDirectories` | Every shipped addon directory, including bundled modules. |
| `gameCompatibility.flavor` | `"forever"` for WoW Forever. |
| `gameCompatibility.interface` | Interface version from the archive TOCs. |
| `passthru.versionToc` | Optional archive path of the main TOC for version discovery. |
| `meta.displayName` | Human-readable name for exported addons. |
| `meta.description` | Brief description of the addon. |
| `meta.homepage` | Canonical upstream project URL. |
| `meta.license` | Upstream license; `lib.licenses.unfree` for All Rights Reserved. |

CurseForge packages use direct CDN URLs and canonical project homepages for updater
compatibility. API discovery belongs in the updater, outside package builds.

Omit `gameCompatibility` when no restriction is declared. Set `passthru.versionToc`
when bundled addons have independent versions. Archives with backslash paths need
a custom `installPhase` that normalizes them to forward slashes.

Fixed bundles use `mkAddonBundle` with `pname`, `version`, `paths` (the component
packages), and `meta`. The builder combines the components' `addonDirectories`
and `srcs`; compatibility remains on each component. Keep separately pinned
component packages under `components/`.

## Validation

`nix build path:.#<slug> --no-link` builds a package, including untracked files.
The installed directories should match the declaration, and `git diff --check`
should pass. Install the built addon in a compatible game client and verify that
it loads without errors and its main functionality works.

Addon commits follow the style `addons: add <slug>`.
