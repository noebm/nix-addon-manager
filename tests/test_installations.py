import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from installer import main as installer


class InstallationsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.game = self.root / "game"
        (self.game / "Interface/AddOns").mkdir(parents=True)
        self.environment = patch.dict(
            os.environ, {"XDG_STATE_HOME": str(self.root / "state")}
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def cli(self, *args):
        output = StringIO()
        with patch("sys.argv", ["installer", *map(str, args)]), redirect_stdout(output):
            installer.main()
        return output.getvalue()

    def test_argument_errors_use_command_name(self):
        errors = StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit) as failure:
            self.cli("--foo")

        self.assertEqual(failure.exception.code, 2)
        self.assertIn("usage: nix-addon-manager ", errors.getvalue())
        self.assertIn("nix-addon-manager: error:", errors.getvalue())

    def client_metadata(self, game):
        (game / "Interface/AddOns").mkdir(parents=True, exist_ok=True)
        (game / ".flavor.info").write_text("wowf\n")
        (game / ".build.info").write_text(
            "Active!DEC:1|Version!STRING:0|Product!STRING:0\n"
            "1|1.60.1.70755|wowf\n"
        )

    def test_discover_nested_clients_and_deduplicate_overlapping_roots(self):
        game = self.root / ".wine/drive_c/World of Warcraft/_forever_"
        self.client_metadata(game)
        alias = self.root / "alias"
        alias.symlink_to(game, target_is_directory=True)

        output = self.cli("discover", self.root, game, alias)

        self.assertEqual(output.count("installation.gamePath ="), 1)
        self.assertIn(f'installation.gamePath = "{game}";', output)
        self.assertIn("forever", output)
        self.assertIn("16001", output)
        self.assertFalse((self.root / "state").exists())

    def test_discover_defaults_to_home_and_skips_invalid_clients(self):
        self.client_metadata(self.game)
        broken = self.root / "broken"
        self.client_metadata(broken)
        (broken / ".build.info").unlink()
        errors = StringIO()

        with patch("pathlib.Path.home", return_value=self.root), redirect_stderr(errors):
            output = self.cli("discover")

        self.assertIn(f'installation.gamePath = "{self.game}";', output)
        self.assertNotIn(f'installation.gamePath = "{broken}";', output)
        self.assertIn(str(broken), errors.getvalue())

    def test_discover_empty_and_missing_roots(self):
        self.assertEqual("No installations found\n", self.cli("discover", self.root))

        with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as failure:
            self.cli("discover", self.root / "missing")

        self.assertEqual(failure.exception.code, 1)

    def test_discover_ignores_other_blizzard_games(self):
        other_game = self.root / "Warcraft III/_retail_"
        other_game.mkdir(parents=True)
        (other_game / ".flavor.info").write_text("w3\n")
        self.client_metadata(self.game)
        errors = StringIO()

        with redirect_stderr(errors):
            output = self.cli("discover", self.root)

        self.assertIn(f'installation.gamePath = "{self.game}";', output)
        self.assertEqual(errors.getvalue(), "")

    def test_discover_escapes_nix_interpolation(self):
        game = self.root / '${name}"'
        self.client_metadata(game)

        self.assertIn(r'\${name}\"', self.cli("discover", game))

    def test_command_arguments_are_scoped(self):
        for arguments in (
            (),
            ("update",),
            ("update", "addons.nix", "--game-path", self.game),
            ("export", "addons.nix"),
            ("recover", "--apply"),
            ("export", "addons.nix", "--output", "addons.zip", "--game-path", self.game),
            ("installations", "list", "--apply"),
        ):
            with self.subTest(arguments=arguments):
                with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as failure:
                    self.cli(*arguments)

                self.assertEqual(failure.exception.code, 2)

    # MIGRATION (manifest schema 1 -> 2): remove with the hidden update option.
    def test_update_game_path_reports_migration_before_evaluating_config(self):
        for option in (
            ("--game-path", str(self.game)),
            (f"--game-path={self.game}",),
        ):
            with self.subTest(option=option):
                errors = StringIO()
                with (
                    patch.object(installer, "nix_manifest") as evaluate,
                    redirect_stderr(errors),
                    self.assertRaises(SystemExit) as failure,
                ):
                    self.cli("update", "addons.nix", *option)

                self.assertEqual(failure.exception.code, 2)
                self.assertIn("--game-path is no longer supported for update", errors.getvalue())
                self.assertIn("gamePath", errors.getvalue())
                self.assertIn("configuration", errors.getvalue())
                evaluate.assert_not_called()

    def test_recover_without_config(self):
        installation = installer.Installation(self.game)
        installer.write_json(installation.state_path, installer.InstallationState())

        with patch.object(installer, "nix_manifest") as evaluate:
            self.assertIn("Recovery complete", self.cli("recover", self.game))

        evaluate.assert_not_called()

    def test_recover_with_config(self):
        installation = installer.Installation(self.game)
        installer.write_json(installation.state_path, installer.InstallationState())

        config = self.root / "addons.nix"
        config.touch()
        manifest = installer.Manifest(gamePath=str(self.game), packages=[])

        with patch.object(installer, "nix_manifest", return_value=manifest):
            self.assertIn("Recovery complete", self.cli("recover", config))

        self.assertTrue(installer.Installation(self.game).control.is_dir())

    def test_recover_rejects_directory_without_game(self):
        directory = self.root / "not-a-game"
        directory.mkdir()
        errors = StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit) as failure:
            self.cli("recover", directory)

        self.assertEqual(failure.exception.code, 1)
        self.assertIn("Game path must contain real Interface/AddOns", errors.getvalue())
        self.assertFalse((self.root / "state").exists())

    def test_recover_rejects_unmanaged_installation_and_leaves_addons_untouched(self):
        addon = self.game / "Interface/AddOns/Unmanaged"
        addon.mkdir()
        contents = addon / "keep.txt"
        contents.write_text("keep")

        for _ in range(2):
            errors = StringIO()
            with redirect_stderr(errors), self.assertRaises(SystemExit) as failure:
                self.cli("recover", self.game)

            self.assertEqual(failure.exception.code, 1)
            self.assertIn("No managed addon installation", errors.getvalue())

        self.assertEqual(contents.read_text(), "keep")
        self.assertFalse(installer.Installation(self.game).state_path.exists())

    def test_recover_first_installation_with_pending_transaction(self):
        installation = installer.Installation(self.game)
        installation.transaction.mkdir()

        self.assertIn("Recovery complete", self.cli("recover", self.game))
        self.assertFalse(installation.transaction.exists())

    @unittest.skipUnless(shutil.which("nix"), "Nix is required")
    def test_recover_rejects_nix_file_without_addon_configuration(self):
        config = self.root / "unrelated.nix"
        config.write_text("{ ... }: { unrelated = true; }")
        errors = StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit) as failure:
            self.cli("recover", config)

        self.assertEqual(failure.exception.code, 1)
        self.assertIn("error:", errors.getvalue())
        self.assertFalse((self.root / "state").exists())

    def test_recover_rejects_missing_target(self):
        errors = StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit) as failure:
            self.cli("recover", self.root / "missing")

        self.assertEqual(failure.exception.code, 1)
        self.assertIn("No such file or directory", errors.getvalue())
        self.assertFalse((self.root / "state").exists())

    def test_cleanup_releases_global_roots_and_skips_pending_and_locked(self):
        saved = {}
        for name in ("existing", "deleted", "pending", "locked", "legacy"):
            game = self.root / name
            (game / "Interface/AddOns").mkdir(parents=True)
            installation = installer.Installation(game)
            roots = installation.control / "roots"
            roots.mkdir()
            old = roots / "old"
            current = roots / "current"
            old.symlink_to("/missing-old")
            current.symlink_to("/missing-current")
            (roots / "unrelated").write_text("keep")
            installer.write_json(
                installation.state_path,
                installer.InstallationState(
                    game=None if name == "legacy" else str(game),
                    manifest=str(current),
                ),
            )
            saved[name] = (installation, old, current)

        shutil.rmtree(self.root / "deleted")
        saved["pending"][0].transaction.mkdir()
        with saved["locked"][0].lock(), redirect_stderr(StringIO()) as errors:
            output = self.cli("cleanup")

        self.assertIn("Cleanup complete", output)
        self.assertIn("Skipping", errors.getvalue())
        for name, (installation, old, current) in saved.items():
            self.assertEqual(old.is_symlink(), name in {"pending", "locked"})
            self.assertEqual(current.is_symlink(), name != "deleted")
            self.assertEqual((old.parent / "unrelated").read_text(), "keep")

    def test_cleanup_finds_roots_without_requiring_hash_directory_names(self):
        control = self.root / "state/nix-addon-manager/legacy-installation"
        roots = control / "roots"
        roots.mkdir(parents=True)
        old = roots / "old"
        old.symlink_to("/missing")
        unrelated = control.parent / "unrelated"
        unrelated.mkdir()
        linked = control.parent / "linked"
        linked.symlink_to(unrelated, target_is_directory=True)

        self.cli("cleanup")

        self.assertFalse(old.is_symlink())
        self.assertFalse((unrelated / "lock").exists())

    def test_cleanup_without_saved_installations(self):
        self.assertIn("Cleanup complete", self.cli("cleanup"))
        self.assertFalse((self.root / "state").exists())

    def test_generation_commands_are_removed(self):
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as failure:
            self.cli("generations", "list")

        self.assertEqual(failure.exception.code, 2)

    def test_installation_commands_are_removed(self):
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as failure:
            self.cli("installations", "list")

        self.assertEqual(failure.exception.code, 2)

    def test_recover_requires_explicit_path(self):
        errors = StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit) as failure:
            self.cli("recover")

        self.assertEqual(failure.exception.code, 2)
        self.assertIn("target", errors.getvalue())

    def test_legacy_registry_is_ignored(self):
        registry = self.root / "state/nix-addon-manager/installations.json"
        registry.parent.mkdir(parents=True)
        registry.write_text("invalid legacy registry")

        with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as failure:
            self.cli("recover", self.game)

        self.assertEqual(failure.exception.code, 1)
        self.assertEqual(registry.read_text(), "invalid legacy registry")
