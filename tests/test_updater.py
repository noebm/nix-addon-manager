import io
import base64
import hashlib
import re
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from updater import main as updater


def release(version, date, *, prerelease=False, asset=True):
    tag = f'spoken/v{version}'
    return {'tag_name': tag, 'published_at': date, 'draft': False,
            'prerelease': prerelease, 'assets': ([{
                'name': f'Spoken-{version}.zip',
                'browser_download_url': f'https://github.com/rusty-key/spoken-wow/releases/download/{tag}/Spoken-{version}.zip',
            }] if asset else [])}


class ReleaseTests(unittest.TestCase):
    current = 'https://github.com/rusty-key/spoken-wow/releases/download/spoken/v3.8.0/Spoken-3.8.0.zip'

    def test_github_skips_prereleases_and_other_components(self):
        releases = [release('4.0.0', '2026-04-01', prerelease=True),
                    release('3.9.0', '2026-03-01'), release('3.8.0', '2026-02-01')]
        releases.append(dict(release('5.0.0', '2026-05-01'), tag_name='quests-audio/v5.0.0'))
        self.assertEqual(updater.github_candidate(self.current, releases)[0],
                         self.current.replace('3.8.0', '3.9.0'))

    def test_github_fails_for_missing_asset_or_current_release(self):
        for releases in ([release('3.9.0', '2026-03-01')],
                         [release('3.9.0', '2026-03-01', asset=False),
                          release('3.8.0', '2026-02-01')]):
            with self.assertRaises(ValueError):
                updater.github_candidate(self.current, releases)

    def test_github_never_downgrades(self):
        self.assertEqual(updater.github_candidate(self.current, [
            release('3.8.0', '2026-02-01'), release('3.7.0', '2026-01-01')]),
            (self.current, '3.8.0'))

    def test_curse_filters_versions_and_release_types(self):
        current = {'id': 10, 'gameVersions': ['1.60.1'], 'fileDate': '2026-01-01'}
        files = [dict(current, id=11, fileDate='2026-02-01', releaseType=1,
                      isAvailable=True, gameVersions=['2.0']),
                 dict(current, id=12, fileDate='2026-03-01', releaseType=2,
                      isAvailable=True),
                 dict(current, id=13, fileDate='2026-04-01', releaseType=1,
                      isAvailable=True, downloadUrl='https://example.org/13.zip')]
        self.assertEqual(updater.curse_candidate(current, files)['id'], 13)
        self.assertEqual(updater.curse_candidate(current, files[:2])['id'], 10)


class ArchiveTests(unittest.TestCase):
    def archive(self, entries):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            for name, value in entries.items():
                archive.writestr(name, value)
        data.seek(0)
        return data

    def test_archive_rejects_escape_links_and_wrong_interface(self):
        for entries in ({'../WTF/config': 'bad'}, {'/absolute/file': 'bad'},
                        {'Test/Test.toc': '## Interface: 99999\n## Version: 2'}):
            with self.assertRaises(ValueError):
                updater.validate_archive(self.archive(entries), 16001)

        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            link = zipfile.ZipInfo('Test/link')
            link.create_system = 3
            link.external_attr = 0o120777 << 16
            archive.writestr(link, '../../WTF')
        data.seek(0)
        with self.assertRaises(ValueError):
            updater.validate_archive(data, None)

    def test_windows_paths_are_normalized_for_directories_and_tocs(self):
        archive = self.archive({
            'AtlasBIStooltips\\': '',
            'AtlasBIStooltips\\AtlasBIStooltips.toc': '## Interface: 16001\n## Version: 2.0\n',
            'AtlasBIStooltips\\AtlasBIStooltips.lua': 'code',
            'AtlasBIStooltips/subdir\\file.lua': 'more code',
        })
        self.assertEqual(updater.validate_archive(archive, 16001), ({'AtlasBIStooltips'}, '2.0'))

    def test_windows_paths_cannot_escape_staging(self):
        for name in ('..\\WTF\\config', 'Test\\..\\..\\WTF/config',
                     '\\absolute\\file', '\\\\server\\share\\file',
                     'C:\\Test\\file', 'C:Test\\file'):
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, 'Unsafe archive entry'):
                    updater.validate_archive(self.archive({name: 'bad'}), None)

    def test_archive_reports_directories_and_version(self):
        self.assertEqual(updater.validate_archive(self.archive({
            'Test/Test.toc': '## Interface: 16001\n## Version: 2.0\n',
            'Test/code.lua': 'code',
        }), 16001), ({'Test'}, '2.0'))


class DownloadTests(unittest.TestCase):
    def test_download_hashes_complete_archive_with_or_without_content_length(self):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w') as output:
            output.writestr('Test/Test.toc', '## Interface: 16001\n## Version: 2.0\n')
        data = archive.getvalue()
        expected_hash = 'sha256-' + base64.b64encode(hashlib.sha256(data).digest()).decode()
        for headers in ({'Content-Length': str(len(data))}, {}):
            with self.subTest(headers=headers):
                response = io.BytesIO(data)
                response.url = 'https://example.org/addon.zip'
                response.headers = headers
                progress = io.StringIO()
                with patch.object(updater, 'urlopen', return_value=response):
                    with patch('sys.stderr', progress):
                        self.assertEqual(updater.download(response.url, 16001),
                                         (expected_hash, {'Test'}, '2.0'))
                self.assertIn('Downloading', progress.getvalue())
                self.assertIn('Validating archive', progress.getvalue())

    def test_download_rejects_insecure_redirect(self):
        response = io.BytesIO(b'not an archive')
        response.url = 'http://example.org/addon.zip'
        with patch.object(updater, 'urlopen', return_value=response):
            with self.assertRaisesRegex(ValueError, 'redirected'):
                updater.download('https://example.org/addon.zip', None)


class UpdateTests(unittest.TestCase):
    def test_preview_preserves_files_and_failed_build_preserves_pins(self):
        import subprocess

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'addons/test/package.nix'
            package.parent.mkdir(parents=True)
            original = 'original pins\n'
            package.write_text(original)
            with patch.object(updater, 'propose', return_value='updated pins\n'):
                updater.update(root, ['test'], apply=False)
                self.assertEqual(package.read_text(), original)
                with patch.object(updater.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'nix')):
                    with self.assertRaises(subprocess.CalledProcessError):
                        updater.update(root, ['test'], apply=True)
                self.assertEqual(package.read_text(), original)

    def test_successful_build_applies_pins_and_rejects_concurrent_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'addons/test/package.nix'
            package.parent.mkdir(parents=True)
            package.write_text('old\n')
            with patch.object(updater, 'propose', return_value='new\n'):
                with patch.object(updater.subprocess, 'run'):
                    updater.update(root, ['test'], apply=True)
                self.assertEqual(package.read_text(), 'new\n')
                package.write_text('old\n')
                with patch.object(updater.subprocess, 'run', side_effect=lambda *a, **k: package.write_text('user edit\n')):
                    with self.assertRaisesRegex(ValueError, 'changed'):
                        updater.update(root, ['test'], apply=True)
                self.assertEqual(package.read_text(), 'user edit\n')


class ProposalTests(unittest.TestCase):
    def test_audio_update_downloads_only_that_component(self):
        root = Path(__file__).resolve().parents[1]
        path = root / 'addons/spoken-english/components/quests-audio/package.nix'
        text = path.read_text()
        source = updater.SOURCE.search(text)
        self.assertIsNotNone(source)
        old_url, old_hash = source.groups()
        old_version = updater.VERSION.search(text)[1]
        fields = old_version.split('.')
        fields[-1] = str(int(fields[-1]) + 1)
        new_version = '.'.join(fields)
        new_url = old_url.replace(old_version, new_version)
        directories = {'SpokenQuestsAudioAlliance', 'SpokenQuestsAudioHorde',
                       'SpokenQuestsAudioShared', 'SpokenQuestsAudioGossip'}
        releases = [
            {'tag_name': f'quests-audio/v{old_version}', 'published_at': '2026-01-01',
             'draft': False, 'prerelease': False, 'assets': []},
            {'tag_name': f'quests-audio/v{new_version}', 'published_at': '2026-02-01',
             'draft': False, 'prerelease': False, 'assets': [{
                 'name': f'SpokenQuestsAudioAll-{new_version}.zip', 'browser_download_url': new_url}]},
        ]
        with patch.object(updater, 'pages', return_value=releases):
            with patch.object(updater, 'download', return_value=('sha256-newhash', directories, None)) as download:
                result = updater.propose('spoken-quests-audio-english', text)
                download.assert_called_once_with(new_url, None)
        self.assertEqual(result, text.replace(old_url, new_url).replace(
            old_hash, 'sha256-newhash').replace(f'version = "{old_version}"', f'version = "{new_version}"'))

    def test_unchanged_component_does_not_download(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / 'addons/spoken-english/components/code/package.nix').read_text()
        version = updater.VERSION.search(text)[1]
        releases = [release(version, '2026-01-01')]
        with patch.object(updater, 'pages', return_value=releases):
            with patch.object(updater, 'download') as download:
                self.assertEqual(updater.propose('spoken', text), text)
                download.assert_not_called()

    def test_changed_component_directories_are_rejected(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / 'addons/spoken-english/components/code/package.nix').read_text()
        version = updater.VERSION.search(text)[1]
        fields = version.split('.')
        fields[-1] = str(int(fields[-1]) + 1)
        newer = '.'.join(fields)
        with patch.object(updater, 'pages', return_value=[
                release(version, '2026-01-01'), release(newer, '2026-02-01')]):
            with patch.object(updater, 'download', return_value=('sha256-new', {'Changed'}, '3.9.0')):
                with self.assertRaisesRegex(ValueError, 'directories changed'):
                    updater.propose('spoken', text)

    def test_components_share_release_list_within_each_run(self):
        root = Path(__file__).resolve().parents[1]
        releases = []
        for path in (root / 'addons/spoken-english/components').glob('*/package.nix'):
            url = updater.SOURCE.search(path.read_text())[1]
            tag = url.split('/download/')[1].rsplit('/', 1)[0]
            releases.append({'tag_name': tag, 'published_at': '2026-01-01',
                             'draft': False, 'prerelease': False, 'assets': []})
        with patch.object(updater, 'pages', return_value=releases) as pages:
            with patch.object(updater, 'download') as download:
                updater.update(root, ['spoken-english'], apply=False)
                pages.assert_called_once_with('https://api.github.com/repos/rusty-key/spoken-wow/releases')
                updater.update(root, ['spoken-english'], apply=False)
                self.assertEqual(pages.call_count, 2)
                download.assert_not_called()

    def test_internal_components_update_through_public_package(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / 'addons/bundle/package.nix'
            bundle.parent.mkdir(parents=True)
            bundle.write_text('bundle definition')
            component = bundle.parent / 'components/code/package.nix'
            component.parent.mkdir(parents=True)
            component.write_text('old pins\n')
            with patch.object(updater, 'propose', return_value='new pins\n') as propose:
                with patch.object(updater.subprocess, 'run') as build:
                    updater.update(root, ['bundle'], apply=True)
                propose.assert_called_once_with('bundle/code', 'old pins\n', {})
                self.assertIn('#bundle', build.call_args.args[0][-1])
            self.assertEqual(component.read_text(), 'new pins\n')
            self.assertEqual(bundle.read_text(), 'bundle definition')


if __name__ == '__main__':
    unittest.main()
