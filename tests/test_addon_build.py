"""Build-time validation of addon package contents."""

from pathlib import Path
import shutil
import subprocess
import unittest


@unittest.skipUnless(shutil.which("nix"), "Nix is required")
class AddonBuildTests(unittest.TestCase):
    def test_declared_directories_require_a_toc(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        cases = [
            ('mkdir -p "$addon"; touch "$addon/Test.toc"', True),
            ('mkdir -p "$addon"; touch "$addon/Test_Vanilla.toc"', True),
            ('mkdir -p "$addon/nested"; touch "$addon/nested/Test.toc"', False),
            ('mkdir -p "$addon/Test.toc"', False),
            ('mkdir -p "$addon"; touch "$addon/Test.lua"', False),
            ('mkdir -p "$out/share/wow-addons/Other"', False),
        ]
        for install, valid in cases:
            with self.subTest(install=install):
                expression = f'''let
                  flake = builtins.getFlake "{repository}";
                  pkgs = import flake.inputs.nixpkgs {{ system = builtins.currentSystem; }};
                  mkAddon = pkgs.callPackage {repository}/lib/mk-addon.nix {{ }};
                in mkAddon {{
                  pname = "toc-validation-test";
                  version = "1";
                  addonDirectories = [ "Test" ];
                  installPhase = ''
                    addon="$out/share/wow-addons/Test"
                    {install}
                  '';
                }}'''
                result = subprocess.run(
                    ["nix", "build", "--impure", "--no-link", "--expr", expression, "-L"],
                    text=True, capture_output=True,
                )

                if valid:
                    self.assertEqual(result.returncode, 0, result.stderr)
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Test", result.stderr)
                    self.assertIn(".toc", result.stderr)


if __name__ == "__main__":
    unittest.main()
