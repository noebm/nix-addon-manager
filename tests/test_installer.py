from dataclasses import asdict
import errno
from io import StringIO
import os
import json
import shutil
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from installer import main as installer
from installer import schemas


class SchemaTests(unittest.TestCase):
    def test_manifest_decodes_nested_metadata(self):
        data = {"schema": 1, "packages": [{
            "name": "test", "version": "1", "path": "/nix/store/test",
            "directories": ["Test"],
            "compatibility": {"flavor": "forever", "version": "1.60.1", "interface": 16001},
            "sources": [{"url": "https://example.org/test.zip", "hash": "abc", "hashAlgorithm": "sha256"}],
        }]}
        manifest = schemas.Manifest.from_dict(data)
        self.assertEqual(manifest.packages[0].compatibility.interface, 16001)
        self.assertEqual(manifest.packages[0].sources[0].hashAlgorithm, "sha256")
        self.assertEqual(asdict(manifest), data)

    def test_legacy_state_and_journal_decode(self):
        state = schemas.InstallationState.from_dict({
            "schema": 1, "directories": {"Test": {
                "name": "test", "version": "1", "path": "/nix/store/test",
            }},
        })
        self.assertEqual(state.directories["Test"].version, "1")
        self.assertIsNone(state.transaction)
        journal = {"id": "generation", "changes": {"Test": {"existed": True}}}
        self.assertEqual(asdict(schemas.TransactionJournal.from_dict(journal)), journal)

    def test_nix_eval_and_build_return_typed_manifests(self):
        data = {"schema": 1, "packages": []}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "manifest.json"
            output.write_text(json.dumps(data))
            with patch.object(installer.subprocess, "check_output", return_value=json.dumps(data)):
                evaluated = installer.nix_manifest(root, root / "config.nix", build=False)
            with patch.object(installer.subprocess, "check_output", return_value=json.dumps([
                {"outputs": {"out": str(output)}},
            ])):
                built = installer.nix_manifest(root, root / "config.nix", build=True, out_link=root / "gc-root")

        self.assertEqual(evaluated, schemas.Manifest(packages=[]))
        self.assertEqual(built, evaluated)

    def test_rejects_unsafe_journal_metadata(self):
        for data in (
            {"id": "../escape", "changes": {}},
            {"id": "generation", "changes": {"../WTF": {"existed": True}}},
            {"id": "generation", "changes": {"Test": {"existed": "false"}}},
        ):
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    schemas.TransactionJournal.from_dict(data)

    def test_unsupported_schemas_are_rejected(self):
        for schema in (schemas.Manifest, schemas.InstallationState):
            with self.subTest(schema=schema.__name__):
                with self.assertRaisesRegex(ValueError, "schema"):
                    schema.from_dict({"schema": 2})


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        environment = patch.dict(os.environ, {"XDG_STATE_HOME": str(self.root / "state")})
        environment.start()
        self.addCleanup(environment.stop)
        self.game = self.root / "game"
        self.target = self.game / "Interface/AddOns"
        self.target.mkdir(parents=True)
        self.control = installer.Installation(self.game).control
        self.source = self.root / "package/share/wow-addons/Test"
        self.source.mkdir(parents=True)
        (self.source / "Test.toc").write_text("version one")
        self.manifest = {"schema": 1, "packages": [{
            "name": "test", "version": "1", "path": str(self.root / "package"),
            "directories": ["Test"],
        }]}

    def run_install(self, apply=True):
        install = installer.Installation(self.game)
        with install.lock() as locked:
            return locked.reconcile(schemas.Manifest.from_dict(self.manifest), apply=apply)

    def test_state_is_external_and_separate_per_game(self):
        self.assertTrue(self.control.is_relative_to(self.root / "state/nix-addon-manager"))
        self.assertFalse((self.game / ".nix-addon-manager").exists())
        other = self.root / "other-game"
        (other / "Interface/AddOns").mkdir(parents=True)
        self.assertNotEqual(self.control, installer.Installation(other).control)
        alias = self.root / "game-alias"
        alias.symlink_to(self.game)
        self.assertEqual(self.control, installer.Installation(alias).control)

    def test_install_update_and_remove_across_filesystems(self):
        rename = Path.rename

        def cross_device(source, destination):
            if source.is_symlink():
                raise OSError(errno.EXDEV, "Cross-device link")
            return rename(source, destination)

        with patch.object(Path, "rename", cross_device):
            self.run_install()
            self.new_version()
            self.run_install()
            self.assertEqual((self.target / "Test/Test.toc").read_text(), "version two")
            self.manifest["packages"] = []
            self.run_install()

        self.assertFalse((self.target / "Test").is_symlink())

    def test_cross_filesystem_install_failure_rolls_back(self):
        unlink = Path.unlink
        rename = Path.rename
        failed = False

        def cross_device(source, destination):
            if source.is_symlink():
                raise OSError(errno.EXDEV, "Cross-device link")
            return rename(source, destination)

        def fail_after_link_creation(path, *args, **kwargs):
            nonlocal failed
            if path.parent.name == "staged" and not failed:
                failed = True
                raise OSError("interrupted after creating destination link")
            return unlink(path, *args, **kwargs)

        with patch.object(Path, "rename", cross_device):
            with patch.object(Path, "unlink", fail_after_link_creation):
                with self.assertRaises(OSError):
                    self.run_install()

        self.assertFalse((self.target / "Test").is_symlink())
        self.assertFalse((self.control / "transaction").exists())
        self.assertEqual((self.source / "Test.toc").read_text(), "version one")

    def test_rejects_state_home_inside_game(self):
        with patch.dict(os.environ, {"XDG_STATE_HOME": str(self.game / "state")}):
            with self.assertRaisesRegex(ValueError, "outside the game"):
                installer.Installation(self.game)

    def test_preview_then_install_and_remove_preserves_unrelated_content(self):
        (self.target / "Other").mkdir()
        (self.game / "WTF").mkdir()
        (self.game / "WTF/settings").write_text("keep")
        self.assertEqual(self.run_install(False), {"Test": installer.Operation.INSTALL})
        self.assertFalse((self.target / "Test").exists())
        self.run_install()
        self.assertTrue((self.target / "Test").is_symlink())
        self.assertEqual((self.target / "Test").readlink(), self.source)
        self.assertEqual((self.target / "Test/Test.toc").read_text(), "version one")
        self.assertEqual(self.run_install(False), {"Test": installer.Operation.KEEP})
        self.manifest["packages"] = []
        self.assertEqual(self.run_install(), {"Test": installer.Operation.REMOVE})
        self.assertTrue((self.target / "Other").is_dir())
        self.assertEqual((self.game / "WTF/settings").read_text(), "keep")

    def test_unmanaged_and_duplicate_ownership_conflict(self):
        (self.target / "Test").mkdir()
        with self.assertRaises(ValueError):
            self.run_install()
        (self.target / "Test").rmdir()
        self.manifest["packages"].append(self.manifest["packages"][0])
        with self.assertRaises(ValueError):
            self.run_install()

    def test_rejects_unsafe_paths_and_links_before_mutation(self):
        self.manifest["packages"][0]["directories"] = ["../WTF"]
        with self.assertRaises(ValueError):
            self.run_install()
        self.manifest["packages"][0]["directories"] = ["Test"]
        (self.source / "escape").symlink_to(self.game)
        with self.assertRaises(ValueError):
            self.run_install()
        self.assertFalse((self.target / "Test").exists())

    def test_failed_update_rolls_back_and_retains_old_state(self):
        self.run_install()
        old_state = (self.control / "state.json").read_text()
        self.manifest["packages"][0]["version"] = "2"
        self.new_version()
        write = installer.write_json

        def fail_commit(path, value):
            if path.name == "state.json":
                raise OSError("interrupted")
            write(path, value)

        with patch.object(installer, "write_json", side_effect=fail_commit):
            with self.assertRaises(OSError):
                self.run_install()
        self.assertEqual((self.target / "Test/Test.toc").read_text(), "version one")
        self.assertEqual((self.control / "state.json").read_text(), old_state)

    def test_interrupted_update_can_be_recovered_on_next_run(self):
        self.run_install()
        self.manifest["packages"][0]["version"] = "2"
        write = installer.write_json

        def fail_commit(path, value):
            if path.name == "state.json":
                raise OSError("interrupted")
            write(path, value)

        with patch.object(installer, "write_json", side_effect=fail_commit):
            with patch.object(installer.LockedInstallation, "recover", side_effect=OSError("killed")):
                with self.assertRaises(OSError):
                    self.run_install()

        with self.assertRaisesRegex(ValueError, "recover"):
            self.run_install()
        install = installer.Installation(self.game)
        with install.lock() as locked:
            locked.recover()
            locked.recover()

        self.assertEqual((self.target / "Test/Test.toc").read_text(), "version one")
        self.assertEqual(self.run_install(False), {"Test": installer.Operation.UPDATE})

    def test_concurrent_operation_is_rejected(self):
        with installer.Installation(self.game).lock():
            with self.assertRaises(ValueError):
                self.run_install()

    def test_lock_is_released_after_exception(self):
        install = installer.Installation(self.game)
        with self.assertRaisesRegex(RuntimeError, "interrupted"):
            with install.lock() as locked:
                raise RuntimeError("interrupted")

        with self.assertRaisesRegex(RuntimeError, "lock context"):
            locked.state()

        self.assertEqual(self.run_install(False), {"Test": installer.Operation.INSTALL})

    def test_operations_are_only_available_on_locked_installation(self):
        install = installer.Installation(self.game)
        for name in ("state", "recover", "reconcile"):
            self.assertFalse(hasattr(install, name))

        with install.lock() as locked:
            self.assertEqual(locked.state(), schemas.InstallationState())
            locked.recover()
            self.assertEqual(locked.reconcile(schemas.Manifest.from_dict(self.manifest)), {"Test": installer.Operation.INSTALL})

    def test_expired_locked_installation_stays_invalid_after_reacquiring(self):
        install = installer.Installation(self.game)
        with install.lock() as expired:
            expired.reconcile(schemas.Manifest.from_dict(self.manifest))

        with install.lock() as current:
            for operation in (
                expired.state,
                expired.recover,
                lambda: expired.reconcile(schemas.Manifest.from_dict(self.manifest), apply=True),
            ):
                with self.assertRaisesRegex(RuntimeError, "lock context"):
                    operation()

            self.assertEqual(current.reconcile(schemas.Manifest.from_dict(self.manifest)), {"Test": installer.Operation.INSTALL})
            self.assertFalse((self.target / "Test").exists())

    def test_class_decorator_guards_new_public_methods(self):
        @installer.requires_active_lock
        class Operations:
            def first(self, value, *, suffix):
                """Return a value with a suffix."""
                return value + suffix

            def second(self):
                return "second"

        operations = Operations()
        with StringIO() as lock:
            operations._lock = lock
            self.assertEqual(operations.first("value", suffix="!"), "value!")
            self.assertEqual(operations.second(), "second")
            first = operations.first

        self.assertEqual(first.__name__, "first")
        self.assertEqual(first.__doc__, "Return a value with a suffix.")
        for operation in (lambda: first("value", suffix="!"), operations.second):
            with self.assertRaisesRegex(RuntimeError, "lock context"):
                operation()

    def test_pending_transaction_blocks_new_operations(self):
        state = self.control
        state.mkdir(exist_ok=True)
        (state / "transaction").mkdir()
        with self.assertRaisesRegex(ValueError, "recover"):
            self.run_install()

    def test_recovery_finishes_committed_transaction(self):
        with patch.object(installer.LockedInstallation, "_archive_transaction", side_effect=OSError("killed")):
            with self.assertRaises(OSError):
                self.run_install()

        install = installer.Installation(self.game)
        with install.lock() as locked:
            locked.recover()

        self.assertEqual(self.run_install(False), {"Test": installer.Operation.KEEP})
        self.assertEqual((self.target / "Test/Test.toc").read_text(), "version one")

    def test_update_retains_previous_content(self):
        self.run_install()
        self.manifest["packages"][0]["version"] = "2"
        self.new_version()
        self.run_install()
        backups = list((self.control / "backups").glob("*/previous/Test/Test.toc"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "version one")
        self.assertEqual((self.target / "Test/Test.toc").read_text(), "version two")

    def new_version(self):
        source = self.root / "package-v2/share/wow-addons/Test"
        source.mkdir(parents=True)
        (source / "Test.toc").write_text("version two")
        self.manifest["packages"][0]["path"] = str(self.root / "package-v2")

    def test_rejects_owned_real_directory(self):
        (self.target / "Test").mkdir()
        (self.target / "Test/custom.lua").write_text("preserve")
        state = self.control
        state.mkdir(exist_ok=True)
        (state / "state.json").write_text(json.dumps({
            "schema": 1, "directories": {name: asdict(owner) for name, owner in
                installer.selected_directories(schemas.Manifest.from_dict(self.manifest)).items()},
        }))
        for apply in (False, True):
            with self.assertRaisesRegex(ValueError, "Expected a managed symlink"):
                self.run_install(apply)

        self.assertEqual((self.target / "Test/custom.lua").read_text(), "preserve")
        self.assertFalse((state / "transaction").exists())

    def test_rejects_changed_link_target(self):
        self.run_install()
        (self.target / "Test").unlink()
        (self.target / "Test").symlink_to(self.game)
        with self.assertRaises(ValueError):
            self.run_install()

    def test_missing_store_target_can_be_repaired_and_deselected(self):
        self.run_install()
        shutil.rmtree(self.source)
        self.assertEqual(self.run_install(False), {"Test": installer.Operation.INSTALL})
        self.manifest["packages"] = []
        self.run_install()
        self.assertFalse((self.target / "Test").is_symlink())

    def test_link_removal_does_not_modify_store_content(self):
        self.run_install()
        self.manifest["packages"] = []
        self.run_install()
        self.assertEqual((self.source / "Test.toc").read_text(), "version one")

    def test_records_and_retains_manifest_root(self):
        root = self.control / "roots/generation"
        root.parent.mkdir(parents=True)
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps(self.manifest))
        root.symlink_to(manifest)
        install = installer.Installation(self.game)
        with install.lock() as locked:
            locked.reconcile(schemas.Manifest.from_dict(self.manifest), apply=True, manifest_root=root)
            self.assertEqual(locked.state().manifest, str(root))
            locked.reconcile(schemas.Manifest(packages=[]), apply=True)

        self.assertTrue(root.is_symlink())
        self.assertTrue(manifest.exists())


if __name__ == "__main__":
    unittest.main()
