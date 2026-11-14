import tempfile
import unittest
from pathlib import Path

from installer.generations import Generations


class GenerationsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.control = Path(self.temporary.name)
        self.directory = self.control / "roots"
        self.directory.mkdir()
        self.target = self.control / "manifest"
        self.target.write_text("manifest")
        self.old = self.directory / "abcd1111"
        self.current = self.directory / "abcd2222"
        self.old.symlink_to(self.target)
        self.current.symlink_to(self.target)
        self.generations = Generations(self.control, str(self.current))

    def test_lists_generations_including_broken_links(self):
        self.target.unlink()
        self.assertEqual(self.generations.entries(), [self.old, self.current])

    def test_remove_unique_prefix_only_unlinks_generation(self):
        self.assertEqual(self.generations.remove("abcd1"), self.old)
        self.assertFalse(self.old.is_symlink())
        self.assertTrue(self.target.exists())
        self.assertTrue(self.current.is_symlink())

    def test_rejects_current_ambiguous_missing_and_path_ids(self):
        for identifier in ("abcd2", "abcd", "missing", "../manifest", ""):
            with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                self.generations.remove(identifier)

        self.assertTrue(self.old.is_symlink())
        self.assertTrue(self.current.is_symlink())

    def test_does_not_treat_real_files_as_generations(self):
        (self.directory / "unrelated").write_text("keep")
        self.assertEqual(self.generations.entries(), [self.old, self.current])

    def test_add_prepares_directory_and_returns_unique_unused_paths(self):
        generations = Generations(self.control / "installation", None)
        generations.control.mkdir()

        first = generations.add()
        second = generations.add()

        self.assertEqual(first.parent, generations.control / "roots")
        self.assertTrue(first.parent.is_dir())
        self.assertNotEqual(first, second)
        self.assertFalse(first.exists())
        self.assertFalse(second.exists())
