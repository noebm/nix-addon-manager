import base64
import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from updater import main as updater
from updater.releases import _api, curseforge, github


def release(version, date, *, prerelease=False, asset=True):
    tag = f"spoken/v{version}"
    return {
        "tag_name": tag,
        "published_at": date,
        "draft": False,
        "prerelease": prerelease,
        "assets": (
            [
                {
                    "name": f"Spoken-{version}.zip",
                    "browser_download_url": f"https://github.com/rusty-key/spoken-wow/releases/download/{tag}/Spoken-{version}.zip",
                }
            ]
            if asset
            else []
        ),
    }


class PaginationTests(unittest.TestCase):
    def test_invalid_entries_warn_without_truncating_pagination(self):
        valid = release("3.8.0", "2026-01-01")
        responses = [[None] * 99 + [valid], [valid]]
        with patch.object(_api, "request_json", side_effect=responses) as request:
            with patch("sys.stderr", new_callable=io.StringIO) as warnings:
                entries = _api.parsed_entries(
                    _api.pages("https://example.org/releases"),
                    github.parse_github_release,
                )
                self.assertEqual(list(entries), [valid, valid])
            self.assertEqual(request.call_count, 2)
            self.assertEqual(warnings.getvalue().count("Warning:"), 99)

    def test_rejects_invalid_page_shapes(self):
        for curse, response in ((False, {}), (True, {"data": {}})):
            with (
                self.subTest(curse=curse),
                patch.object(_api, "request_json", return_value=response),
                self.assertRaisesRegex(TypeError, "Expected JSON array"),
            ):
                list(_api.pages("https://example.org/releases", curse=curse))

    def test_parses_release_and_rejects_invalid_nested_fields(self):
        value = release("3.8.0", "2026-01-01")
        self.assertEqual(github.parse_github_release(value), value)
        value["assets"][0]["name"] = 42
        with self.assertRaisesRegex(ValueError, "name.*str"):
            github.parse_github_release(value)

    def test_curse_file_optional_fields_are_checked(self):
        value = {"id": 10, "gameVersions": ["1.60.1"], "fileDate": "2026-01-01"}
        self.assertEqual(curseforge.parse_curse_file(value), value)
        for field, invalid in (
            ("id", True),
            ("isAvailable", "yes"),
            ("gameVersions", [1]),
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                curseforge.parse_curse_file(dict(value, **{field: invalid}))

    def test_pages_yields_lazily_across_pages(self):
        for curse, page_size in ((False, 100), (True, 50)):
            with self.subTest(curse=curse):
                first = [{"id": index} for index in range(page_size)]
                last = [{"id": page_size}]
                responses = [first, last]
                if curse:
                    responses = [{"data": values} for values in responses]
                with patch.object(
                    _api, "request_json", side_effect=responses
                ) as request:
                    entries = _api.pages("https://example.org/releases", curse=curse)
                    request.assert_not_called()
                    self.assertEqual(next(entries), first[0])
                    self.assertEqual(request.call_count, 1)
                    self.assertEqual(list(entries), first[1:] + last)
                    self.assertEqual(request.call_count, 2)


class ReleaseTests(unittest.TestCase):
    current = "https://github.com/rusty-key/spoken-wow/releases/download/spoken/v3.8.0/Spoken-3.8.0.zip"

    def test_github_skips_prereleases_and_other_components(self):
        releases = [
            release("4.0.0", "2026-04-01", prerelease=True),
            release("3.9.0", "2026-03-01"),
            release("3.8.0", "2026-02-01"),
        ]
        releases.append(
            dict(release("5.0.0", "2026-05-01"), tag_name="quests-audio/v5.0.0")
        )
        self.assertEqual(
            github.github_candidate(self.current, releases)[0],
            self.current.replace("3.8.0", "3.9.0"),
        )

    def test_github_fails_for_missing_asset_or_current_release(self):
        for releases in (
            [release("3.9.0", "2026-03-01")],
            [
                release("3.9.0", "2026-03-01", asset=False),
                release("3.8.0", "2026-02-01"),
            ],
        ):
            with self.assertRaises(ValueError):
                github.github_candidate(self.current, releases)

    def test_github_never_downgrades(self):
        self.assertEqual(
            github.github_candidate(
                self.current,
                [release("3.8.0", "2026-02-01"), release("3.7.0", "2026-01-01")],
            ),
            (self.current, "3.8.0"),
        )

    def test_github_selects_highest_numeric_version_regardless_of_dates_or_order(self):
        releases = [
            release("3.8.0", "2026-03-01"),
            release("3.10.0", "2026-01-01"),
            release("3.9.0", "2026-05-01"),
            release("3.7.1", "2026-06-01"),
            release("3.10.0.1", "2026-02-01"),
        ]
        for ordered in (releases, list(reversed(releases))):
            with self.subTest(reversed=ordered != releases):
                self.assertEqual(
                    github.github_candidate(self.current, ordered),
                    (self.current.replace("3.8.0", "3.10.0.1"), "3.10.0.1"),
                )

    def test_github_ignores_drafts_and_non_numeric_tags(self):
        releases = [
            release("3.8.0", "2026-01-01"),
            dict(release("9.0.0", "2026-03-01"), draft=True),
            release("nightly", "2026-04-01"),
            release("3.9.0", "2026-02-01"),
        ]
        self.assertEqual(
            github.github_candidate(self.current, releases),
            (self.current.replace("3.8.0", "3.9.0"), "3.9.0"),
        )

    def test_curse_filters_versions_and_release_types(self):
        current = {"id": 10, "gameVersions": ["1.60.1"], "fileDate": "2026-01-01"}
        files = [
            dict(
                current,
                id=11,
                fileDate="2026-02-01",
                releaseType=1,
                isAvailable=True,
                gameVersions=["2.0"],
            ),
            dict(
                current, id=12, fileDate="2026-03-01", releaseType=2, isAvailable=True
            ),
            dict(
                current,
                id=13,
                fileDate="2026-04-01",
                releaseType=1,
                isAvailable=True,
                downloadUrl="https://example.org/13.zip",
            ),
        ]
        self.assertEqual(curseforge.curse_candidate(current, files)["id"], 13)
        self.assertEqual(curseforge.curse_candidate(current, files[:2])["id"], 10)


class CurseDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.current = {
            "id": 10,
            "gameVersions": ["1.60.1", "1.60.2"],
            "fileDate": "2026-01-01",
            "releaseType": 1,
            "isAvailable": True,
        }

    def test_index_fetches_matching_stable_files_once_without_pagination(self):
        project = {
            "id": 123,
            "latestFilesIndexes": [
                {"fileId": 13, "gameVersion": version, "releaseType": kind}
                for version, kind in (
                    ("1.60.1", 1),
                    ("1.60.2", 1),
                    ("2.0", 1),
                    ("1.60.1", 2),
                )
            ],
        }
        latest = dict(self.current, id=13, fileDate="2026-02-01")
        with patch.object(
            _api, "request_json", return_value={"data": latest}
        ) as request:
            self.assertEqual(curseforge.curse_latest(self.current, project), latest)
            request.assert_called_once_with(
                "https://api.curseforge.com/v1/mods/123/files/13"
            )

    def test_current_index_entry_needs_no_file_history(self):
        project = {
            "id": 123,
            "latestFilesIndexes": [
                {"fileId": 10, "gameVersion": "1.60.1", "releaseType": 1}
            ],
        }
        with patch.object(_api, "request_json") as request:
            self.assertEqual(
                curseforge.curse_latest(self.current, project), self.current
            )
            request.assert_not_called()

    def test_missing_or_unusable_index_falls_back_to_filtered_history(self):
        latest = dict(self.current, id=12, fileDate="2026-02-01")
        for indexes in (
            None,
            [],
            [{"fileId": 13, "gameVersion": "1.60.1", "releaseType": 1}],
        ):
            with self.subTest(indexes=indexes):
                project = {"id": 123}
                if indexes is not None:
                    project["latestFilesIndexes"] = indexes

                def response(url):
                    if url.endswith("/13"):
                        return {"data": dict(latest, id=13, isAvailable=False)}
                    self.assertIn("gameVersion=1.60.", url)
                    return {"data": [latest]}

                with patch.object(_api, "request_json", side_effect=response):
                    self.assertEqual(
                        curseforge.curse_latest(self.current, project), latest
                    )


class ArchiveTests(unittest.TestCase):
    def archive(self, entries):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as archive:
            for name, value in entries.items():
                archive.writestr(name, value)
        data.seek(0)
        return data

    def test_archive_rejects_escape_links_and_wrong_interface(self):
        for entries in (
            {"../WTF/config": "bad"},
            {"/absolute/file": "bad"},
            {"Test/Test.toc": "## Interface: 99999\n## Version: 2"},
        ):
            with self.assertRaises(ValueError):
                updater.validate_archive(self.archive(entries), 16001)

        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as archive:
            link = zipfile.ZipInfo("Test/link")
            link.create_system = 3
            link.external_attr = 0o120777 << 16
            archive.writestr(link, "../../WTF")
        data.seek(0)
        with self.assertRaises(ValueError):
            updater.validate_archive(data, None)

    def test_windows_paths_are_normalized_for_directories_and_tocs(self):
        archive = self.archive(
            {
                "AtlasBIStooltips\\": "",
                "AtlasBIStooltips\\AtlasBIStooltips.toc": "## Interface: 16001\n## Version: 2.0\n",
                "AtlasBIStooltips\\AtlasBIStooltips.lua": "code",
                "AtlasBIStooltips/subdir\\file.lua": "more code",
            }
        )
        self.assertEqual(
            updater.validate_archive(archive, 16001), ({"AtlasBIStooltips"}, "2.0")
        )

    def test_explicit_version_toc_ignores_bundled_addon_versions(self):
        for names in (
            ["AtlasBIStooltips", "AtlasLootClassic"],
            ["AtlasLootClassic", "AtlasBIStooltips"],
        ):
            entries = {
                f"{name}\\{name}.toc": (
                    "## Interface: 16001\n## Version: "
                    + ("v1.3.4" if name == "AtlasLootClassic" else "2.0")
                )
                for name in names
            }
            with self.subTest(names=names):
                self.assertEqual(
                    updater.validate_archive(
                        self.archive(entries),
                        16001,
                        version_toc="AtlasLootClassic/AtlasLootClassic.toc",
                    ),
                    (set(names), "1.3.4"),
                )

    def test_explicit_version_toc_must_exist_and_have_version(self):
        for entries in (
            {"Other/Other.toc": "## Interface: 16001\n## Version: 2.0"},
            {"Main/Main.toc": "## Interface: 16001"},
        ):
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                updater.validate_archive(
                    self.archive(entries), 16001, version_toc="Main/Main.toc"
                )

    def test_windows_paths_cannot_escape_staging(self):
        for name in (
            "..\\WTF\\config",
            "Test\\..\\..\\WTF/config",
            "\\absolute\\file",
            "\\\\server\\share\\file",
            "C:\\Test\\file",
            "C:Test\\file",
        ):
            with (
                self.subTest(name=name),
                self.assertRaisesRegex(ValueError, "Unsafe archive entry"),
            ):
                updater.validate_archive(self.archive({name: "bad"}), None)

    def test_archive_reports_directories_and_version(self):
        self.assertEqual(
            updater.validate_archive(
                self.archive(
                    {
                        "Test/Test.toc": "## Interface: 16001\n## Version: 2.0\n",
                        "Test/code.lua": "code",
                    }
                ),
                16001,
            ),
            ({"Test"}, "2.0"),
        )


class DirectoryDiscoveryTests(ArchiveTests):
    def test_range_discovery_reads_only_part_of_archive(self):
        data = self.archive(
            {
                "New/New.toc": "## Interface: 16001\n## Version: 2\n",
                "New/audio.bin": b"x" * 300000,
            }
        ).getvalue()
        transferred = []

        def respond(request, **kwargs):
            start, end = map(int, request.get_header("Range")[6:].split("-"))
            end = min(end, len(data) - 1)
            response = io.BytesIO(data[start : end + 1])
            response.url = request.full_url
            response.status = 206
            response.headers = {"Content-Range": f"bytes {start}-{end}/{len(data)}"}
            transferred.append(end - start + 1)
            return response

        with patch.object(updater, "urlopen", side_effect=respond):
            self.assertEqual(
                updater.discover_directories("https://example.org/addon.zip", 16001),
                ({"New"}, "2"),
            )
        self.assertLess(sum(transferred), len(data) // 2)

    def test_unsupported_ranges_fall_back_to_full_download(self):
        response = io.BytesIO(b"ignored range")
        response.url = "https://example.org/addon.zip"
        response.status = 200
        response.headers = {}
        with (
            patch.object(updater, "urlopen", return_value=response),
            patch.object(updater, "download", return_value=("hash", {"New"}, "2")),
        ):
            self.assertEqual(
                updater.discover_directories(response.url, None), ({"New"}, "2")
            )

    def test_invalid_partial_responses_fall_back(self):
        for headers, body in (
            ({"Content-Range": "bytes 1-1/10"}, b"x"),
            ({"Content-Range": "bytes 0-0/10"}, b""),
            ({}, b"x"),
        ):
            response = io.BytesIO(body)
            response.url = "https://example.org/addon.zip"
            response.status = 206
            response.headers = headers
            with (
                self.subTest(headers=headers, body=body),
                patch.object(updater, "urlopen", return_value=response),
                patch.object(updater, "download", return_value=("hash", {"New"}, "2")),
            ):
                self.assertEqual(
                    updater.discover_directories(response.url, None),
                    ({"New"}, "2"),
                )

    def test_rejected_range_falls_back(self):
        error = updater.HTTPError(
            "https://example.org/addon.zip", 501, "Unsupported", {}, None
        )
        with (
            patch.object(updater, "urlopen", side_effect=error),
            patch.object(updater, "download", return_value=("hash", {"New"}, "2")),
        ):
            self.assertEqual(
                updater.discover_directories(error.url, None), ({"New"}, "2")
            )

    def test_partial_discovery_rejects_insecure_redirect(self):
        response = io.BytesIO(b"x")
        response.url = "http://example.org/addon.zip"
        with (
            patch.object(updater, "urlopen", return_value=response),
            self.assertRaisesRegex(ValueError, "redirected"),
        ):
            updater.discover_directories("https://example.org/addon.zip", None)


class DownloadTests(unittest.TestCase):
    def test_download_hashes_complete_archive_with_or_without_content_length(self):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("Test/Test.toc", "## Interface: 16001\n## Version: 2.0\n")
        data = archive.getvalue()
        expected_hash = (
            "sha256-" + base64.b64encode(hashlib.sha256(data).digest()).decode()
        )
        for headers in ({"Content-Length": str(len(data))}, {}):
            with self.subTest(headers=headers):
                response = io.BytesIO(data)
                response.url = "https://example.org/addon.zip"
                response.headers = headers
                progress = io.StringIO()
                with (
                    patch.object(updater, "urlopen", return_value=response),
                    patch("sys.stderr", progress),
                ):
                    self.assertEqual(
                        updater.download(response.url, 16001),
                        (expected_hash, {"Test"}, "2.0"),
                    )
                self.assertIn("Downloading", progress.getvalue())
                self.assertIn("Validating archive", progress.getvalue())

    def test_download_rejects_insecure_redirect(self):
        response = io.BytesIO(b"not an archive")
        response.url = "http://example.org/addon.zip"
        with (
            patch.object(updater, "urlopen", return_value=response),
            self.assertRaisesRegex(ValueError, "redirected"),
        ):
            updater.download("https://example.org/addon.zip", None)


class UpdateTests(unittest.TestCase):
    def test_preview_preserves_files_and_failed_build_preserves_pins(self):
        import subprocess

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "addons/test/package.nix"
            package.parent.mkdir(parents=True)
            original = "original pins\n"
            package.write_text(original)
            with patch.object(updater, "propose", return_value=("updated pins\n", [])):
                updater.update(root, ["test"], apply=False)
                self.assertEqual(package.read_text(), original)
                with (
                    patch.object(
                        updater.subprocess,
                        "run",
                        side_effect=subprocess.CalledProcessError(1, "nix"),
                    ),
                    self.assertRaises(subprocess.CalledProcessError),
                ):
                    updater.update(root, ["test"], apply=True)
                self.assertEqual(package.read_text(), original)

    def test_digest_archive_is_validated_before_build_and_pin_write(self):
        import subprocess

        for addon in ("Test", "Unexpected"):
            with self.subTest(addon=addon), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                package = root / "addons/test/package.nix"
                package.parent.mkdir(parents=True)
                package.write_text("old\n")
                archive = root / "release.zip"
                with zipfile.ZipFile(archive, "w") as output:
                    output.writestr(f"{addon}/{addon}.toc", "## Interface: 16001\n")

                def proposal(*args):
                    return "new\n", [
                        updater.PendingValidation(
                            url="https://example.org/release.zip",
                            digest="sha256-test",
                            interface=16001,
                            directories={"Test"},
                        )
                    ]

                prefetched = subprocess.CompletedProcess(
                    [], 0, stdout=updater.json.dumps({"storePath": str(archive)})
                )
                with (
                    patch.object(updater, "propose", side_effect=proposal),
                    patch.object(
                        updater.subprocess, "run", return_value=prefetched
                    ) as run,
                ):
                    if addon == "Test":
                        updater.update(root, ["test"], apply=True)
                        self.assertEqual(run.call_count, 2)
                        self.assertEqual(package.read_text(), "new\n")
                    else:
                        with self.assertRaisesRegex(ValueError, "directories changed"):
                            updater.update(root, ["test"], apply=True)
                        self.assertEqual(run.call_count, 1)
                        self.assertEqual(package.read_text(), "old\n")
                    self.assertEqual(
                        run.call_args_list[0].args[0],
                        [
                            "nix",
                            "store",
                            "prefetch-file",
                            "--json",
                            "--expected-hash",
                            "sha256-test",
                            "https://example.org/release.zip",
                        ],
                    )

    def test_successful_build_applies_pins_and_rejects_concurrent_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "addons/test/package.nix"
            package.parent.mkdir(parents=True)
            package.write_text("old\n")
            with patch.object(updater, "propose", return_value=("new\n", [])):
                with patch.object(updater.subprocess, "run"):
                    updater.update(root, ["test"], apply=True)
                self.assertEqual(package.read_text(), "new\n")
                package.write_text("old\n")
                with (
                    patch.object(
                        updater.subprocess,
                        "run",
                        side_effect=lambda *a, **k: package.write_text("user edit\n"),
                    ),
                    self.assertRaisesRegex(ValueError, "changed"),
                ):
                    updater.update(root, ["test"], apply=True)
                self.assertEqual(package.read_text(), "user edit\n")


class ProposalTests(unittest.TestCase):
    def test_audio_update_downloads_only_that_component(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "addons/spoken-english/components/quests-audio/package.nix"
        text = path.read_text()
        source = updater.SOURCE.search(text)
        self.assertIsNotNone(source)
        old_url, old_hash = source.groups()
        old_version = updater.VERSION.search(text)[1]
        fields = old_version.split(".")
        fields[-1] = str(int(fields[-1]) + 1)
        new_version = ".".join(fields)
        new_url = old_url.replace(old_version, new_version)
        directories = {
            "SpokenQuestsAudioAlliance",
            "SpokenQuestsAudioHorde",
            "SpokenQuestsAudioShared",
            "SpokenQuestsAudioGossip",
        }
        releases = [
            {
                "tag_name": f"quests-audio/v{old_version}",
                "published_at": "2026-01-01",
                "draft": False,
                "prerelease": False,
                "assets": [],
            },
            {
                "tag_name": f"quests-audio/v{new_version}",
                "published_at": "2026-02-01",
                "draft": False,
                "prerelease": False,
                "assets": [
                    {
                        "name": f"SpokenQuestsAudioAll-{new_version}.zip",
                        "browser_download_url": new_url,
                    }
                ],
            },
        ]
        with (
            patch.object(_api, "pages", return_value=releases),
            patch.object(
                updater, "download", return_value=("sha256-newhash", directories, None)
            ) as download,
        ):
            result, _ = updater.propose(
                "spoken-quests-audio-english", text, updater.releases.Retriever()
            )
            download.assert_called_once_with(new_url, None, version_toc=None)
        self.assertEqual(
            result,
            text.replace(old_url, new_url)
            .replace(old_hash, "sha256-newhash")
            .replace(f'version = "{old_version}"', f'version = "{new_version}"'),
        )

    def test_github_digest_discovers_directories_and_converts_to_sri(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "addons/spoken-english/components/code/package.nix").read_text()
        version = updater.VERSION.search(text)[1]
        newer = version + ".1"
        latest = release(newer, "2026-02-01")
        latest["assets"][0]["digest"] = "sha256:" + "ab" * 32
        expected = "sha256-" + base64.b64encode(bytes.fromhex("ab" * 32)).decode()
        with (
            patch.object(
                _api, "pages", return_value=[release(version, "2026-01-01"), latest]
            ),
            patch.object(updater, "discover_directories", return_value=({"New"}, None)),
            patch.object(updater, "download") as download,
        ):
            result, validations = updater.propose(
                "spoken", text, updater.releases.Retriever()
            )
            download.assert_not_called()
        self.assertEqual(
            validations,
            [
                updater.PendingValidation(
                    url=latest["assets"][0]["browser_download_url"],
                    digest=expected,
                    interface=None,
                    directories={"New"},
                )
            ],
        )
        self.assertIn(expected, result)
        self.assertIn(f'version = "{newer}"', result)

    def test_malformed_github_digest_is_rejected(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "addons/spoken-english/components/code/package.nix").read_text()
        version = updater.VERSION.search(text)[1]
        latest = release(version + ".1", "2026-02-01")
        latest["assets"][0]["digest"] = "sha256:invalid"
        with (
            patch.object(
                _api, "pages", return_value=[release(version, "2026-01-01"), latest]
            ),
            self.assertRaisesRegex(ValueError, "digest"),
        ):
            updater.propose("spoken", text, updater.releases.Retriever())

    def test_unchanged_component_does_not_download(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "addons/spoken-english/components/code/package.nix").read_text()
        version = updater.VERSION.search(text)[1]
        releases = [release(version, "2026-01-01")]
        with (
            patch.object(_api, "pages", return_value=releases),
            patch.object(updater, "download") as download,
        ):
            self.assertEqual(
                updater.propose("spoken", text, updater.releases.Retriever()),
                (text, []),
            )
            download.assert_not_called()

    def test_changed_component_directories_are_recorded(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "addons/spoken-english/components/code/package.nix").read_text()
        version = updater.VERSION.search(text)[1]
        fields = version.split(".")
        fields[-1] = str(int(fields[-1]) + 1)
        newer = ".".join(fields)
        with (
            patch.object(
                _api,
                "pages",
                return_value=[
                    release(version, "2026-01-01"),
                    release(newer, "2026-02-01"),
                ],
            ),
            patch.object(
                updater, "download", return_value=("sha256-new", {"Changed"}, "3.9.0")
            ),
        ):
            result, _ = updater.propose("spoken", text, updater.releases.Retriever())
            self.assertIn('addonDirectories = [\n      "Changed"\n    ];', result)

    def test_components_share_release_list_within_each_run(self):
        root = Path(__file__).resolve().parents[1]
        releases = []
        for path in (root / "addons/spoken-english/components").glob("*/package.nix"):
            url = updater.SOURCE.search(path.read_text())[1]
            tag = url.split("/download/")[1].rsplit("/", 1)[0]
            releases.append(
                {
                    "tag_name": tag,
                    "published_at": "2026-01-01",
                    "draft": False,
                    "prerelease": False,
                    "assets": [],
                }
            )
        with (
            patch.object(_api, "pages", return_value=releases) as pages,
            patch.object(updater, "download") as download,
        ):
            updater.update(root, ["spoken-english"], apply=False)
            pages.assert_called_once_with(
                "https://api.github.com/repos/rusty-key/spoken-wow/releases"
            )
            updater.update(root, ["spoken-english"], apply=False)
            self.assertEqual(pages.call_count, 2)
            download.assert_not_called()

    def test_internal_components_update_through_public_package(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "addons/bundle/package.nix"
            bundle.parent.mkdir(parents=True)
            bundle.write_text("bundle definition")
            component = bundle.parent / "components/code/package.nix"
            component.parent.mkdir(parents=True)
            component.write_text("old pins\n")
            with patch.object(
                updater, "propose", return_value=("new pins\n", [])
            ) as propose:
                with patch.object(updater.subprocess, "run") as build:
                    updater.update(root, ["bundle"], apply=True)
                propose.assert_called_once()
                self.assertEqual(
                    propose.call_args.args[:2], ("bundle/code", "old pins\n")
                )
                self.assertIsInstance(
                    propose.call_args.args[2], updater.releases.Retriever
                )
                self.assertIn("#bundle", build.call_args.args[0][-1])
            self.assertEqual(component.read_text(), "new pins\n")
            self.assertEqual(bundle.read_text(), "bundle definition")


if __name__ == "__main__":
    unittest.main()
