"""GitHub component release parsing and selection."""

import base64
import re
from typing import NotRequired, TypedDict

from . import _api
from ._api import JSON, field, json_dict, json_list


class GitHubAsset(TypedDict):
    name: str
    browser_download_url: str
    digest: NotRequired[str | None]


class GitHubRelease(TypedDict):
    tag_name: str
    published_at: str
    draft: bool
    prerelease: bool
    assets: list[GitHubAsset]


def parse_github_release(value: JSON) -> GitHubRelease:
    record = json_dict(value)
    assets: list[GitHubAsset] = []
    for asset_value in json_list(record.get("assets")):
        asset = json_dict(asset_value)
        parsed: GitHubAsset = {
            "name": field(asset, "name", str),
            "browser_download_url": field(asset, "browser_download_url", str),
        }
        if "digest" in asset:
            parsed["digest"] = (
                None if asset["digest"] is None else field(asset, "digest", str)
            )
        assets.append(parsed)
    return {
        "tag_name": field(record, "tag_name", str),
        "published_at": field(record, "published_at", str),
        "draft": field(record, "draft", bool),
        "prerelease": field(record, "prerelease", bool),
        "assets": assets,
    }


def github_candidate(url: str, releases: list[GitHubRelease]) -> tuple[str, str]:
    match = re.fullmatch(
        r"https://github.com/([^/]+/[^/]+)/releases/download/(.+)/([^/]+)", url
    )
    if not match:
        raise ValueError(f"Unsupported GitHub release URL: {url}")
    _repository, tag, filename = match.groups()
    component, separator, version = tag.rpartition("/v")
    if not separator or version not in filename:
        raise ValueError(f"Unsupported component tag: {tag}")
    current = next(
        (release for release in releases if release["tag_name"] == tag), None
    )
    if current is None:
        raise ValueError(f"Pinned release {tag} missing upstream; refusing to guess")

    def numeric(value: str) -> tuple[int, ...]:
        if not re.fullmatch(r"\d+(?:\.\d+)*", value):
            raise ValueError(f"Unsupported release version: {value}")
        return tuple(map(int, value.split(".")))

    current_version = numeric(version)
    prefix = component + "/v"
    candidates = [
        release
        for release in releases
        if not release["draft"]
        and not release["prerelease"]
        and release["tag_name"].startswith(prefix)
        and re.fullmatch(r"\d+(?:\.\d+)*", release["tag_name"][len(prefix) :])
    ]
    if not candidates:
        return url, version
    latest = max(
        candidates, key=lambda release: numeric(release["tag_name"][len(prefix) :])
    )
    new_version = latest["tag_name"][len(prefix) :]

    if numeric(new_version) <= current_version:
        return url, version
    expected = filename.replace(version, new_version)
    assets = [asset for asset in latest["assets"] if asset["name"] == expected]
    if len(assets) != 1:
        raise ValueError(
            f"Expected exactly one {expected} asset in {latest['tag_name']}"
        )
    return assets[0]["browser_download_url"], new_version


def retrieve(
    url: str, cache: dict[str, list[GitHubRelease]]
) -> tuple[str, str, str | None]:
    """Find a component update, caching repository metadata for this run."""
    repository = "/".join(url.split("/")[3:5])
    if repository not in cache:
        cache[repository] = list(
            _api.parsed_entries(
                _api.pages(f"https://api.github.com/repos/{repository}/releases"),
                parse_github_release,
            )
        )
    candidate, version = github_candidate(url, cache[repository])
    assets = [
        asset
        for release in cache[repository]
        for asset in release["assets"]
        if asset["browser_download_url"] == candidate
    ]
    digest = assets[0].get("digest") if len(assets) == 1 else None
    if digest:
        if not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest):
            raise ValueError(f"Invalid GitHub asset digest: {candidate}")
        digest = "sha256-" + base64.b64encode(bytes.fromhex(digest[7:])).decode()
    return candidate, version, digest
