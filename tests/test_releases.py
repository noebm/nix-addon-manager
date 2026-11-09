import io
import unittest
from unittest.mock import patch

from updater import releases
from updater.releases import _api


class RetrievalTests(unittest.TestCase):
    def test_curseforge_retrieval_skips_invalid_projects_and_returns_release(self):
        current = {
            "id": 1001,
            "gameVersions": ["1.60.1"],
            "fileDate": "2026-01-01",
        }
        latest = dict(
            current,
            id=1002,
            fileDate="2026-02-01",
            releaseType=1,
            isAvailable=True,
            downloadUrl="https://edge.forgecdn.net/files/1/2/Addon.zip",
        )
        project = {
            "id": 123,
            "slug": "addon",
            "latestFilesIndexes": [
                {"fileId": 1002, "gameVersion": "1.60.1", "releaseType": 1}
            ],
        }
        with (
            patch.object(
                _api,
                "request_json",
                side_effect=[
                    {"data": [None, project]},
                    {"data": current},
                    {"data": latest},
                ],
            ),
            patch("sys.stderr", new_callable=io.StringIO) as warnings,
        ):
            result = releases.Retriever().retrieve(
                "https://edge.forgecdn.net/files/1/1/Addon.zip",
                homepage="https://www.curseforge.com/wow/addons/addon",
            )
        self.assertEqual(result, releases.Release(url=latest["downloadUrl"]))
        self.assertIn("Warning:", warnings.getvalue())

    def test_unsupported_sources_and_missing_homepage_fail_before_requests(self):
        retriever = releases.Retriever()
        with patch.object(_api, "request_json") as request:
            for url in (
                "https://example.org/addon.zip",
                "https://edge.forgecdn.net/files/1/1/Addon.zip",
            ):
                with self.subTest(url=url), self.assertRaises(ValueError):
                    retriever.retrieve(url)
            request.assert_not_called()
