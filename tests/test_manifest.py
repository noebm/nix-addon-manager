"""Integration checks for the evaluated Nix installation manifest."""

from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import unittest

from installer.main import nix_manifest, selected_directories


@unittest.skipUnless(shutil.which("nix"), "Nix is required")
class ManifestTests(unittest.TestCase):
    def test_ordinary_packages_are_rejected_as_addons(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        selections = [
            "pkgs.hello",
            '(pkgs.hello.overrideAttrs { passthru.addonDirectories = "Hello"; })',
            '(pkgs.hello.overrideAttrs { passthru.addonDirectories = [ 123 ]; })',
            '(addons.spoken-english.overrideAttrs (old: { passthru = old.passthru // { paths = [ pkgs.hello ]; }; }))',
        ]
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "addons.nix"
            for selection in selections:
                with self.subTest(selection=selection):
                    configuration.write_text(
                        '{ pkgs, addons, ... }: { installation.gamePath = "/game"; '
                        f'installation.addons = [ {selection} ]; }}'
                    )
                    result = subprocess.run(
                        [
                            "nix", "eval", "--impure", "--json", "--expr",
                            f"import {repository / 'lib/manifest.nix'} {{ "
                            f"repository = {json.dumps(str(repository))}; "
                            f"installationFile = {json.dumps(str(configuration))}; build = false; }}",
                        ],
                        text=True, capture_output=True,
                    )

                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("installation.addons", result.stderr)
                    self.assertIn("addon package", result.stderr)

    # MIGRATION (manifest schema 1 -> 2): remove with the list-only guidance.
    def test_old_configuration_reports_how_to_migrate(self):
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "addons.nix"
            configuration.write_text("{ addons, ... }: [ addons.books-on-map-forever ]")
            result = subprocess.run(
                [
                    "nix", "eval", "--impure", "--json", "--expr",
                    f"import {repository / 'lib/manifest.nix'} {{ "
                    f"repository = {json.dumps(str(repository))}; "
                    f"installationFile = {json.dumps(str(configuration))}; build = false; }}",
                ],
                text=True, capture_output=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("List-only addon configurations are no longer supported", result.stderr)
        self.assertIn('installation.gamePath = "/path/to/WoW/_forever_";', result.stderr)
        self.assertIn("installation.addons = [", result.stderr)

    def test_root_options_are_rejected(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "addons.nix"
            configuration.write_text('{ ... }: { gamePath = "/game"; addons = []; }')
            result = subprocess.run(
                [
                    "nix", "eval", "--impure", "--json", "--expr",
                    f"import {repository / 'lib/manifest.nix'} {{ "
                    f"repository = {json.dumps(str(repository))}; "
                    f"installationFile = {json.dumps(str(configuration))}; build = false; }}",
                ],
                text=True, capture_output=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not exist", result.stderr)

    def test_configuration_requires_game_path(self):
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "addons.nix"
            for expression in ("{ ... }: []", "{ ... }: { installation.addons = []; }"):
                with self.subTest(expression=expression):
                    configuration.write_text(expression)
                    with self.assertRaises(subprocess.CalledProcessError):
                        nix_manifest(repository, configuration)

    def test_invalid_configuration_reports_validation_error(self):
        repository = Path(__file__).resolve().parents[1]
        shape_error = "addons"
        path_error = "gamePath"
        cases = [
            ('{ installation.gamePath = "/game"; }', shape_error),
            ('{ installation = { gamePath = "/game"; addons = null; }; }', shape_error),
            ("{ installation.addons = []; }", path_error),
            ('{ installation = { gamePath = "/game"; addons = [ 123 ]; }; }', shape_error),
            ('{ installation = { gamePath = "/game"; addons = []; typo = true; }; }', "typo"),
            *[(f"{{ installation = {{ addons = []; gamePath = {value}; }}; }}", path_error)
              for value in ('null', '123', '""', './.')],
        ]
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "addons.nix"
            for selection, message in cases:
                with self.subTest(selection=selection):
                    configuration.write_text("{ ... }: " + selection)
                    result = subprocess.run(
                        [
                            "nix", "eval", "--impure", "--json", "--expr",
                            f"import {repository / 'lib/manifest.nix'} {{ "
                            f"repository = {json.dumps(str(repository))}; "
                            f"installationFile = {json.dumps(str(configuration))}; build = false; }}",
                        ],
                        text=True, capture_output=True,
                    )

                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(message, result.stderr)

    def test_configuration_supports_module_imports_and_merging(self):
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "addons.nix"
            (Path(directory) / "base.nix").write_text('''{ lib, addons, ... }: {
              installation.gamePath = lib.mkDefault "/default";
              installation.addons = [ addons.books-on-map-forever ];
            }''')
            configuration.write_text('''{ config, ... }: {
              imports = [ ./base.nix ];
              config = {
                installation.gamePath = "/game";
                installation.addons = if config.installation.gamePath == "/game" then [] else throw "wrong path";
              };
            }''')
            manifest = nix_manifest(repository, configuration)

        self.assertEqual(manifest.gamePath, "/game")
        self.assertEqual(len(manifest.packages), 1)

    def test_configuration_contains_game_path_and_addons(self):
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "addons.nix"
            configuration.write_text('''{ addons, ... }: {
              installation.gamePath = "/games/WoW/_forever_";
              installation.addons = [ addons.books-on-map-forever ];
            }''')
            manifest = nix_manifest(repository, configuration)

        self.assertEqual(manifest.gamePath, "/games/WoW/_forever_")
        self.assertEqual(len(manifest.packages), 1)

    def test_spoken_code_update_preserves_audio_and_ordinary_addons(self):
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "addons.nix"
            configuration.write_text("""{ addons, ... }: { installation.gamePath = "/games/WoW"; installation.addons = [
              addons.books-on-map-forever
              addons.spoken-english
            ]; }""")
            before = nix_manifest(repository, configuration)
            self.assertEqual(len(before.packages), 6)

            configuration.write_text("""{ addons, ... }: { installation.gamePath = "/games/WoW"; installation.addons = [
              addons.books-on-map-forever
              (addons.spoken-english.overrideAttrs (old: {
                passthru = old.passthru // {
                  paths = map (component:
                    if component.pname == "spoken" then
                      component.overrideAttrs { version = "test-update"; }
                    else component
                  ) old.passthru.paths;
                };
              }))
            ]; }""")
            after = nix_manifest(repository, configuration)

        previous = selected_directories(before)
        selected = selected_directories(after)
        self.assertEqual(previous.keys(), selected.keys())
        changed = {name for name in previous if previous[name] != selected[name]}
        self.assertEqual(
            changed,
            {
                "Spoken",
                "SpokenContributions",
                "Spoken_Bosses",
                "Spoken_Places",
                "Spoken_Quests",
                "Spoken_Readables",
            },
        )


if __name__ == "__main__":
    unittest.main()
