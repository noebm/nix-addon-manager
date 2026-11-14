"""Integration checks for the evaluated Nix installation manifest."""

from pathlib import Path
import shutil
import tempfile
import unittest

from installer.main import nix_manifest, selected_directories


@unittest.skipUnless(shutil.which("nix"), "Nix is required")
class ManifestTests(unittest.TestCase):
    def test_spoken_code_update_preserves_audio_and_ordinary_addons(self):
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "addons.nix"
            configuration.write_text("""{ addons, ... }: [
              addons.books-on-map-forever
              addons.spoken-english
            ]""")
            before = nix_manifest(repository, configuration)
            self.assertEqual(len(before.packages), 6)

            configuration.write_text("""{ addons, ... }: [
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
            ]""")
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
