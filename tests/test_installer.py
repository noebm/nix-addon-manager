from dataclasses import asdict
import errno
from io import StringIO
import os
import json
import shutil
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from installer import main as installer
from installer import schemas


class SchemaTests(unittest.TestCase):
    def test_manifest_decodes_nested_metadata(self):
        data = {
            "schema": 1,
            "packages": [
                {
                    "name": "test",
                    "version": "1",
                    "path": "/nix/store/test",
                    "directories": ["Test"],
                    "compatibility": {"flavor": "forever", "interface": 16001},
                    "sources": [
                        {
                            "url": "https://example.org/test.zip",
                            "hash": "abc",
                            "hashAlgorithm": "sha256",
                        }
                    ],
                }
            ],
        }
        manifest = schemas.Manifest.from_dict(data)
        self.assertEqual(manifest.packages[0].compatibility.interface, 16001)
        self.assertEqual(manifest.packages[0].sources[0].hashAlgorithm, "sha256")
        self.assertEqual(asdict(manifest), data)

    def test_compatibility_has_one_numeric_version(self):
        compatibility = schemas.GameCompatibility(flavor="forever", interface=16001)
        self.assertEqual(
            asdict(compatibility), {"flavor": "forever", "interface": 16001}
        )

    def test_legacy_state_and_journal_decode(self):
        state = schemas.InstallationState.from_dict(
            {
                "schema": 1,
                "directories": {
                    "Test": {
                        "name": "test",
                        "version": "1",
                        "path": "/nix/store/test",
                    }
                },
            }
        )
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
            with patch.object(
                installer.subprocess, "check_output", return_value=json.dumps(data)
            ):
                evaluated = installer.nix_manifest(root, root / "config.nix")
            with patch.object(
                installer.subprocess,
                "check_output",
                return_value=json.dumps(
                    [
                        {"outputs": {"out": str(output)}},
                    ]
                ),
            ):
                built = installer.nix_manifest(
                    root, root / "config.nix", out_link=root / "gc-root"
                )

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


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "package/share/wow-addons/Test"
        self.source.mkdir(parents=True)
        (self.source / "Test.toc").write_text("addon content")
        (self.source / "empty").mkdir()
        self.manifest = schemas.Manifest.from_dict(
            {
                "schema": 1,
                "packages": [
                    {
                        "name": "test",
                        "version": "1",
                        "path": str(self.root / "package"),
                        "directories": ["Test"],
                    }
                ],
            }
        )
        self.output = self.root / "addons.zip"

    def test_export_cli_without_game_path(self):
        config = self.root / "addons.nix"
        config.touch()
        with patch(
            "sys.argv",
            ["installer", "--config", str(config), "--export-zip", str(self.output)],
        ):
            with patch.object(installer, "nix_manifest", return_value=self.manifest):
                with patch.object(
                    installer,
                    "Installation",
                    side_effect=AssertionError("game accessed"),
                ):
                    with patch("sys.stdout", new_callable=StringIO) as output:
                        installer.main()

        self.assertEqual(
            output.getvalue().splitlines(),
            [
                "exported: test 1",
                f"Export complete: {self.output}",
            ],
        )
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(archive.read("Test/Test.toc"), b"addon content")
            self.assertIn("Test/empty/", archive.namelist())
            self.assertEqual(
                archive.getinfo("Test/Test.toc").compress_type, zipfile.ZIP_DEFLATED
            )

    def test_export_cli_rejects_existing_destination_before_build(self):
        config = self.root / "addons.nix"
        config.touch()
        for kind in ("file", "directory", "dangling symlink"):
            with self.subTest(kind=kind):
                destination = self.root / kind
                if kind == "file":
                    destination.write_bytes(b"existing")
                elif kind == "directory":
                    destination.mkdir()
                else:
                    destination.symlink_to(self.root / "missing")

                with patch(
                    "sys.argv",
                    [
                        "installer",
                        "--config",
                        str(config),
                        "--export-zip",
                        str(destination),
                    ],
                ):
                    with patch.object(installer, "nix_manifest") as build:
                        with patch("sys.stderr", new_callable=StringIO) as error:
                            with self.assertRaises(SystemExit) as exited:
                                installer.main()

                self.assertEqual(exited.exception.code, 1)
                self.assertIn("File exists", error.getvalue())
                build.assert_not_called()

    def test_export_rejects_conflicts_and_unsafe_content(self):
        duplicate = schemas.Manifest(packages=self.manifest.packages * 2)
        with self.assertRaisesRegex(ValueError, "ownership"):
            installer.export_zip(duplicate, self.output)

        (self.source / "unsafe").symlink_to(self.root)
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            installer.export_zip(self.manifest, self.output)

        self.assertFalse(self.output.exists())

    def test_export_preserves_existing_output(self):
        self.output.write_bytes(b"existing")
        with self.assertRaises(FileExistsError):
            installer.export_zip(self.manifest, self.output)

        self.assertEqual(self.output.read_bytes(), b"existing")

    def test_failed_export_leaves_no_partial_archive(self):
        with patch.object(zipfile.ZipFile, "write", side_effect=OSError("interrupted")):
            with self.assertRaises(OSError):
                installer.export_zip(self.manifest, self.output)

        self.assertFalse(self.output.exists())
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["package"])


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        environment = patch.dict(
            os.environ, {"XDG_STATE_HOME": str(self.root / "state")}
        )
        environment.start()
        self.addCleanup(environment.stop)
        self.game = self.root / "game"
        self.target = self.game / "Interface/AddOns"
        self.target.mkdir(parents=True)
        self.control = installer.Installation(self.game).control
        self.source = self.root / "package/share/wow-addons/Test"
        self.source.mkdir(parents=True)
        (self.source / "Test.toc").write_text("version one")
        self.manifest = {
            "schema": 1,
            "packages": [
                {
                    "name": "test",
                    "version": "1",
                    "path": str(self.root / "package"),
                    "directories": ["Test"],
                }
            ],
        }

    def run_install(self, apply=True):
        install = installer.Installation(self.game)
        with install.lock() as locked:
            return locked.reconcile(
                schemas.Manifest.from_dict(self.manifest), apply=apply
            )

    def client_metadata(self, *, product="wowf", version="1.60.1.70755", parent=True):
        (self.game / ".flavor.info").write_text(
            "Product Flavor!STRING:0\n" + product + "\n"
        )
        location = self.game.parent if parent else self.game
        (location / ".build.info").write_text(
            "Branch!STRING:0|Active!DEC:1|Version!STRING:0|Product!STRING:0\n"
            "eu|1|12.0.0.12345|wow\n"
            f"eu|1|{version}|{product}\n"
            f"us|0|0.0.0.1|{product}\n"
        )
        self.manifest["packages"][0]["compatibility"] = {
            "flavor": "forever",
            "interface": 16001,
        }

    def test_matching_client_metadata_allows_preview_and_apply(self):
        for parent in (True, False):
            with self.subTest(parent=parent):
                self.client_metadata(parent=parent)
                self.run_install(False)
                self.run_install()
        self.assertEqual((self.target / "Test/Test.toc").read_text(), "version one")

    def test_flavor_metadata_accepts_plain_product_and_rejects_ambiguous_rows(self):
        self.client_metadata()
        for content in ("wowf\n", "\ufeffProduct Flavor!STRING:0\r\nwowf\r\n"):
            (self.game / ".flavor.info").write_text(content)
            self.run_install(False)

        for content in (
            "Product Flavor!STRING:0\n",
            "Product Flavor!STRING:0\nwowf\nwow\n",
            "Wrong Header\nwowf\n",
        ):
            (self.game / ".flavor.info").write_text(content)
            with self.subTest(content=content):
                with self.assertRaisesRegex(ValueError, "Invalid game product"):
                    self.run_install(False)

    def test_client_mismatches_block_preview_and_apply_without_changes(self):
        self.client_metadata()
        self.run_install()
        old_state = (self.control / "state.json").read_text()
        self.new_version()
        for field, value in (("flavor", "retail"), ("interface", 16002)):
            self.client_metadata()
            self.manifest["packages"][0]["compatibility"][field] = value
            for apply in (False, True):
                with self.subTest(field=field, apply=apply):
                    with self.assertRaisesRegex(ValueError, f"test.*{field}"):
                        self.run_install(apply)
                    self.assertEqual(
                        (self.control / "state.json").read_text(), old_state
                    )
                    self.assertEqual(
                        (self.target / "Test/Test.toc").read_text(), "version one"
                    )
                    self.assertFalse((self.control / "transaction").exists())

    def test_outdated_addons_warn_and_allow_preview_and_apply(self):
        self.client_metadata()
        self.manifest["packages"][0]["compatibility"].update(interface=10900)
        for apply in (False, True):
            with (
                self.subTest(apply=apply),
                patch("sys.stderr", new_callable=StringIO) as warnings,
            ):
                self.assertEqual(
                    self.run_install(apply), {"Test": installer.Operation.INSTALL}
                )
                self.assertIn("warning: test: out of date", warnings.getvalue())
                self.assertIn("10900", warnings.getvalue())
                self.assertIn("16001", warnings.getvalue())
        self.assertEqual((self.target / "Test/Test.toc").read_text(), "version one")

    def test_partial_compatibility_declarations_warn_for_older_targets(self):
        for compatibility in (
            {"interface": 16000},
            {"flavor": "forever", "interface": 16000},
        ):
            self.client_metadata()
            self.manifest["packages"][0]["compatibility"] = compatibility
            with self.subTest(compatibility=compatibility):
                with patch("sys.stderr", new_callable=StringIO) as warnings:
                    self.run_install(False)
                self.assertIn("out of date", warnings.getvalue())

    def test_matching_client_does_not_warn(self):
        self.client_metadata()
        with patch("sys.stderr", new_callable=StringIO) as warnings:
            self.run_install(False)
        self.assertEqual(warnings.getvalue(), "")

    def test_missing_or_ambiguous_client_metadata_blocks_declared_compatibility(self):
        self.client_metadata()
        (self.game / ".flavor.info").unlink()
        with self.assertRaisesRegex(ValueError, "flavor.info"):
            self.run_install()
        self.client_metadata()
        (self.root / ".build.info").unlink()
        with self.assertRaisesRegex(ValueError, "build.info"):
            self.run_install()
        self.client_metadata()
        with (self.root / ".build.info").open("a") as stream:
            stream.write("eu|1|1.60.2.12345|wowf\n")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            self.run_install()
        self.assertFalse((self.target / "Test").exists())

    def test_build_metadata_must_match_selected_product(self):
        self.client_metadata()
        (self.game / ".flavor.info").write_text("wow_classic_era")
        with self.assertRaisesRegex(ValueError, "wow_classic_era"):
            self.run_install()
        self.assertFalse((self.target / "Test").exists())

    def test_malformed_build_metadata_is_rejected(self):
        for content in (
            "wrong header\n",
            "Active|Version|Product\n1|garbage|wowf\n",
            "Active|Version|Product\n1|1.60.1.123|wowf|extra\n",
        ):
            self.client_metadata()
            (self.root / ".build.info").write_text(content)
            with self.subTest(content=content):
                with self.assertRaises(ValueError):
                    self.run_install()
        self.assertFalse((self.target / "Test").exists())

    def test_identical_regional_build_rows_are_not_ambiguous(self):
        self.client_metadata()
        with (self.root / ".build.info").open("a") as stream:
            stream.write("us|1|1.60.1.70755|wowf\n")
        self.run_install()

    def test_forever_beta_is_identified_by_product_and_version(self):
        self.client_metadata(product="wow_classic_beta")
        self.run_install()
        self.client_metadata(product="wow_classic_beta", version="5.5.0.12345")
        self.manifest["packages"][0]["compatibility"] = {"flavor": "forever"}
        with self.assertRaisesRegex(ValueError, "flavor"):
            self.run_install()

    def test_removal_and_recovery_do_not_require_client_metadata(self):
        self.client_metadata()
        self.run_install()
        (self.game / ".flavor.info").unlink()
        with installer.Installation(self.game).lock() as locked:
            locked.recover()
        self.manifest["packages"] = []
        self.run_install()
        self.assertFalse((self.target / "Test").exists())

    def test_state_is_external_and_separate_per_game(self):
        self.assertTrue(
            self.control.is_relative_to(self.root / "state/nix-addon-manager")
        )
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
            with patch.object(
                installer.LockedInstallation, "recover", side_effect=OSError("killed")
            ):
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
            self.assertEqual(
                locked.reconcile(schemas.Manifest.from_dict(self.manifest)),
                {"Test": installer.Operation.INSTALL},
            )

    def test_expired_locked_installation_stays_invalid_after_reacquiring(self):
        install = installer.Installation(self.game)
        with install.lock() as expired:
            expired.reconcile(schemas.Manifest.from_dict(self.manifest))

        with install.lock() as current:
            for operation in (
                expired.state,
                expired.recover,
                lambda: expired.reconcile(
                    schemas.Manifest.from_dict(self.manifest), apply=True
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "lock context"):
                    operation()

            self.assertEqual(
                current.reconcile(schemas.Manifest.from_dict(self.manifest)),
                {"Test": installer.Operation.INSTALL},
            )
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
        with patch.object(
            installer.LockedInstallation,
            "_archive_transaction",
            side_effect=OSError("killed"),
        ):
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
        (state / "state.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "directories": {
                        name: asdict(owner)
                        for name, owner in installer.selected_directories(
                            schemas.Manifest.from_dict(self.manifest)
                        ).items()
                    },
                }
            )
        )
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
            locked.reconcile(
                schemas.Manifest.from_dict(self.manifest),
                apply=True,
                manifest_root=root,
            )
            self.assertEqual(locked.state().manifest, str(root))
            locked.reconcile(schemas.Manifest(packages=[]), apply=True)

        self.assertTrue(root.is_symlink())
        self.assertTrue(manifest.exists())


if __name__ == "__main__":
    unittest.main()
