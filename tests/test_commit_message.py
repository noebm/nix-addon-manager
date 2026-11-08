from pathlib import Path
import subprocess
import tempfile
import unittest

from updater.commit_message import staged_message


class CommitMessageTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.git('init', '--quiet')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.org')

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, text=True)

    def package(self, path, name, version, digest='old'):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f'{{\n  pname = "{name}";\n  version = "{version}";\n  hash = "{digest}";\n}}\n')

    def baseline(self):
        self.git('add', '.')
        self.git('commit', '--quiet', '-m', 'baseline')

    def test_message_uses_staged_versions_and_internal_component_names(self):
        code = 'addons/spoken-english/components/code/package.nix'
        books = 'addons/books/package.nix'
        self.package(code, 'spoken', '3.8.0')
        self.package(books, 'books-on-map-forever', '2.2.1')
        self.baseline()
        self.package(code, 'spoken', '3.8.3')
        self.package(books, 'books-on-map-forever', '2.2.2')
        self.git('add', 'addons')
        self.package(code, 'spoken', '9.9.9')
        self.assertEqual(staged_message(self.root),
                         'addons: update books-on-map-forever, spoken\n\n'
                         '- books-on-map-forever: 2.2.1 -> 2.2.2\n'
                         '- spoken: 3.8.0 -> 3.8.3\n')

    def test_hash_only_change(self):
        path = 'addons/test/package.nix'
        self.package(path, 'test', '1.0')
        self.baseline()
        self.package(path, 'test', '1.0', digest='new')
        self.git('add', '.')
        self.assertEqual(staged_message(self.root),
                         'addons: update test\n\n- test: refresh source pins (1.0)\n')

    def test_empty_selection_is_rejected(self):
        (self.root / 'README.md').write_text('baseline')
        self.baseline()
        with self.assertRaisesRegex(ValueError, 'No staged addon'):
            staged_message(self.root)


if __name__ == '__main__':
    unittest.main()
