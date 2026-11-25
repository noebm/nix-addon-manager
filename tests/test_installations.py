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

    def test_generations_operate_globally_and_can_be_scoped(self):
        other = self.root / "other"
        (other / "Interface/AddOns").mkdir(parents=True)
        saved = []
        for index, game in enumerate((self.game, other)):
            installation = installer.Installation(game)
            roots = installation.control / "roots"
            roots.mkdir()
            old = roots / f"abcd{index}"
            current = roots / f"current{index}"
            old.symlink_to("/missing-old")
            current.symlink_to("/missing-current")
            installer.write_json(
                installation.state_path,
                installer.InstallationState(game=str(game), manifest=str(current)),
            )
            saved.append((old, current))

        output = self.cli("generations", "list")
        self.assertIn("abcd0", output)
        self.assertIn("abcd1", output)
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            self.cli("generations", "remove", "abcd")
        self.assertTrue(all(old.is_symlink() for old, _ in saved))
        self.cli("generations", "remove", "abcd0")
        self.assertFalse(saved[0][0].is_symlink())
        saved[0][0].symlink_to("/missing-old")
        self.cli("generations", "prune", "--game-path", self.game)
        self.assertFalse(saved[0][0].is_symlink())
        self.assertTrue(saved[1][0].is_symlink())
        (other / "Interface/AddOns").rmdir()
        (other / "Interface").rmdir()
        other.rmdir()
        self.cli("generations", "prune")
        self.assertFalse(saved[1][0].is_symlink())
        self.assertTrue(saved[0][1].is_symlink())
        self.assertFalse(saved[1][1].is_symlink())
        self.assertIn("No generations", self.cli("generations", "list", "--game-path", other))

    def test_global_prune_checks_transactions_before_removing_roots(self):
        roots = []
        for name in ("first", "second"):
            game = self.root / name
            (game / "Interface/AddOns").mkdir(parents=True)
            installation = installer.Installation(game)
            directory = installation.control / "roots"
            directory.mkdir()
            old = directory / "old"
            old.symlink_to("/missing")
            roots.append(old)

        installation.transaction.mkdir()
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            self.cli("generations", "prune")

        self.assertTrue(all(root.is_symlink() for root in roots))

    def test_generations_commands_accept_game_path(self):
        installation = installer.Installation(self.game)
        roots = installation.control / "roots"
        roots.mkdir()
        old = roots / "aaaa1111"
        current = roots / "bbbb2222"
        old.symlink_to("/nix/store/old-manifest")
        current.symlink_to("/nix/store/current-manifest")
        installer.write_json(
            installation.state_path, installer.InstallationState(manifest=str(current))
        )

        output = self.cli("generations", "list")
        self.assertIn("Generations:", output)
        self.assertIn("aaaa1111", output)
        self.assertIn("bbbb2222 (current)", output)
        self.assertIn(
            "Removed generation: aaaa1111",
            self.cli("generations", "remove", "aaaa", "--game-path", self.game),
        )
        self.assertFalse(old.is_symlink())
        self.assertTrue(current.is_symlink())

        old.symlink_to("/nix/store/old-manifest")
        self.assertIn(
            "Removed generation: aaaa1111",
            self.cli("generations", "prune"),
        )
        self.assertFalse(old.is_symlink())
        self.assertTrue(current.is_symlink())
        self.assertIn("No old generations", self.cli("generations", "prune"))

    def test_generations_prune_without_current_preserves_unrelated_files(self):
        installation = installer.Installation(self.game)
        roots = installation.control / "roots"
        roots.mkdir()
        old = roots / "old"
        old.symlink_to("/missing-manifest")
        unrelated = roots / "unrelated"
        unrelated.write_text("keep")

        self.assertIn("Removed generation: old", self.cli("generations", "prune"))
        self.assertFalse(old.is_symlink())
        self.assertEqual(unrelated.read_text(), "keep")
        self.assertIn("No old generations", self.cli("generations", "prune"))

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
        self.assertIn("No generations", self.cli("generations", "list"))
        self.assertEqual(registry.read_text(), "invalid legacy registry")
