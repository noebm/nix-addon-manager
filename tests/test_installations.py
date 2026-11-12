import json
import os
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from installer import main as installer
from installer.installations import InstallationPath, InstallationRegistry
from installer.schemas import RegistryDocument, RegisteredInstallation


class InstallationsTests(unittest.TestCase):
    def test_installation_path_formats_path_and_identifier(self):
        installation = InstallationPath("id", Path("/game"))
        self.assertEqual(f"{installation}", "/game (id)")

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

    def registry(self):
        return json.loads(
            (self.root / "state/nix-addon-manager/installations.json").read_text()
        )

    def test_loads_registration_with_legacy_metadata(self):
        registry_path = self.root / "state/nix-addon-manager/installations.json"
        registry_path.parent.mkdir(parents=True)
        registry_path.write_text(
            json.dumps({
                "schema": 1,
                "installations": {
                    "id": {"game": "/game", "flavor": "forever", "interface": 16001}
                },
                "default": "id",
            })
        )

        registry = InstallationRegistry.from_environment()
        self.assertEqual(registry._document.installations["id"].game, "/game")
        self.assertEqual(registry._document.default, "id")

    def test_edits_reload_registry_before_saving(self):
        first = InstallationRegistry.from_environment()
        second = InstallationRegistry.from_environment()
        with first.edit():
            first._document.installations["first"] = RegisteredInstallation("/first")
            first._document.default = "first"

        with second.edit():
            second._document.installations["second"] = RegisteredInstallation("/second")

        self.assertEqual(
            self.registry(),
            {
                "schema": 1,
                "installations": {
                    "first": {"game": "/first"},
                    "second": {"game": "/second"},
                },
                "default": "first",
            },
        )

    def test_rejects_unsupported_registry_schema(self):
        with self.assertRaisesRegex(ValueError, "Unsupported installation registry schema"):
            RegistryDocument(schema=2)

        registry_path = self.root / "state/nix-addon-manager/installations.json"
        registry_path.parent.mkdir(parents=True)
        registry_path.write_text(json.dumps({"schema": 2, "installations": {}}))

        with self.assertRaisesRegex(ValueError, "Unsupported installation registry schema"):
            InstallationRegistry.from_environment()

    def test_registration_default_selection_and_removal(self):
        output = self.cli("installations", "add", self.game)
        identifier = next(iter(self.registry()["installations"]))
        self.assertEqual(output, f"Installation {self.game} ({identifier[:4]}) has been added\n")
        entry = self.registry()["installations"][identifier]
        self.assertEqual(entry, {"game": str(self.game)})
        self.assertIn(f"({identifier[:4]})", self.cli("installations", "list"))
        self.assertIn(f"({identifier})", self.cli("installations", "list", "--full"))
        self.cli("installations", "default", identifier)
        self.assertEqual(self.registry()["default"], identifier)
        with patch.object(
            installer, "nix_manifest", return_value=installer.Manifest(packages=[])
        ):
            config = self.root / "addons.nix"
            config.touch()
            self.assertIn("Preview only", self.cli("--config", config))
            self.assertIn(
                "Preview only", self.cli("--game-path", identifier, "--config", config)
            )
        self.cli("installations", "remove", self.game)
        self.assertEqual(self.registry()["installations"], {})
        self.assertIsNone(self.registry()["default"])
        self.assertTrue(self.game.is_dir())

    def test_short_identifiers_resolve_for_all_commands(self):
        self.cli("installations", "add", self.game)
        identifier = next(iter(self.registry()["installations"]))
        prefix = identifier[:4]
        self.cli("installations", "default", prefix)
        registry = InstallationRegistry.from_environment()
        self.assertEqual(registry.resolve_game_path(Path(prefix)), self.game)
        self.assertEqual(self.registry()["default"], identifier)
        self.assertIn(f"({identifier})", self.cli("installations", "remove", prefix, "--full"))
        self.assertEqual(self.registry()["installations"], {})

    def test_colliding_prefixes_extend_display_and_reject_ambiguity(self):
        registry = InstallationRegistry.from_environment()
        with registry.edit():
            registry._document.installations = {
                "abcd1" + "0" * 59: RegisteredInstallation(str(self.game)),
                "abcd2" + "0" * 59: RegisteredInstallation("/other"),
            }

        output = self.cli("installations", "list")
        self.assertIn("(abcd1)", output)
        self.assertIn("(abcd2)", output)
        before = self.registry()
        for arguments in (("installations", "default", "abcd"),
                          ("installations", "remove", "abcd"),
                          ("--game-path", "abcd", "--recover")):
            errors = StringIO()
            with redirect_stderr(errors), self.assertRaises(SystemExit):
                self.cli(*arguments)
            self.assertIn("Ambiguous installation ID", errors.getvalue())
            self.assertEqual(self.registry(), before)

    def test_alias_registration_does_not_duplicate(self):
        self.cli("installations", "add", self.game)
        alias = self.root / "alias"
        alias.symlink_to(self.game)
        self.cli("installations", "add", alias)
        entries = self.registry()["installations"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(next(iter(entries.values())), {"game": str(self.game)})
        self.cli("installations", "default", alias)
        # A missing game can still be unregistered by ID.
        identifier = next(iter(entries))
        self.game.rename(self.root / "moved")
        self.cli("installations", "remove", identifier)

    def test_invalid_registration_does_not_publish_registry(self):
        (self.game / "Interface/AddOns").rmdir()
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            self.cli("installations", "add", self.game)
        self.assertFalse((self.root / "state/nix-addon-manager/installations.json").exists())

    def test_empty_list(self):
        self.assertIn("No installations", self.cli("installations", "list"))

    def test_registry_commands_return_results_without_printing(self):
        registry = InstallationRegistry.from_environment()
        output = StringIO()
        errors = StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            installation = registry.add(self.game)
            identifier = installation.identifier
            self.assertIsInstance(identifier, str)
            self.assertEqual(installation, InstallationPath(identifier, self.game))
            self.assertEqual(registry.list_installations(), [(installation, False)])
            self.assertEqual(registry.set_default(str(self.game)), installation)
            self.assertEqual(registry.list_installations(), [(installation, True)])
            self.assertEqual(registry.remove(identifier), installation)
            self.assertEqual(registry.list_installations(), [])
            self.assertIsNone(registry.default_game_path)
            self.assertIsNone(registry.set_default(identifier))
            self.assertIsNone(registry.remove(identifier))

        self.assertEqual(output.getvalue(), "")
        self.assertEqual(errors.getvalue(), "")

    def test_missing_lookups_return_none(self):
        registry = InstallationRegistry.from_environment()
        self.assertIsNone(registry._resolve_identifier(str(self.game)))
        self.assertIsNone(registry.default_game_path)

    def test_default_game_path_is_separate_from_explicit_resolution(self):
        registry = InstallationRegistry(
            self.root,
            RegistryDocument(
                installations={"id": RegisteredInstallation(str(self.game))},
                default="id",
            ),
        )

        self.assertEqual(registry.default_game_path, self.game)
        self.assertEqual(registry.resolve_game_path(Path("id")), self.game)
        self.assertEqual(registry.resolve_game_path(Path("~/other")), Path.home() / "other")

    def test_removing_missing_installation_succeeds(self):
        self.cli("installations", "add", self.game)
        self.cli("installations", "remove", self.game)
        before = self.registry()

        self.assertIn("already absent", self.cli("installations", "remove", self.game))
        self.assertEqual(self.registry(), before)

    def test_missing_default_selection_fails_without_changing_default(self):
        self.cli("installations", "add", self.game)
        self.cli("installations", "default", self.game)
        before = self.registry()
        errors = StringIO()

        with redirect_stderr(errors), self.assertRaises(SystemExit) as failure:
            self.cli("installations", "default", self.root / "unknown")

        self.assertEqual(failure.exception.code, 1)
        self.assertIn("Installation is not registered", errors.getvalue())
        self.assertEqual(self.registry(), before)

    def test_missing_default_reports_cli_error(self):
        errors = StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit) as failure:
            self.cli("--config", self.root / "addons.nix")

        self.assertEqual(failure.exception.code, 1)
        self.assertIn("No default installation", errors.getvalue())

    def test_default_command_prints_current_path_without_changing_registry(self):
        self.cli("installations", "add", self.game)
        self.cli("installations", "default", self.game)
        before = self.registry()

        self.assertEqual(self.cli("installations", "default"), f"{self.game}\n")
        self.assertEqual(self.registry(), before)

    def test_default_command_without_default_reports_error(self):
        errors = StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit) as failure:
            self.cli("installations", "default")

        self.assertEqual(failure.exception.code, 1)
        self.assertIn("No default installation", errors.getvalue())
        self.assertFalse((self.root / "state/nix-addon-manager/installations.json").exists())
