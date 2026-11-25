import os
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
        self.assertIn("Recovery complete", self.cli("recover", "--game-path", self.game))

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
        self.assertTrue(all(current.is_symlink() for _, current in saved))
        self.assertIn("current1", self.cli("generations", "list", "--game-path", other))

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
        self.assertIn("--game-path", errors.getvalue())

    def test_legacy_registry_is_ignored(self):
        registry = self.root / "state/nix-addon-manager/installations.json"
        registry.parent.mkdir(parents=True)
        registry.write_text("invalid legacy registry")

        self.assertIn("Recovery complete", self.cli("recover", "--game-path", self.game))
        self.assertIn("No generations", self.cli("generations", "list"))
        self.assertEqual(registry.read_text(), "invalid legacy registry")
