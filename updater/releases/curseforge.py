"""CurseForge project discovery and compatible release selection."""

import re
import sys
from collections.abc import Iterable
from typing import NotRequired, TypedDict
from urllib.parse import urlencode

from . import _api
from ._api import JSON, field, json_dict, json_list


class CurseFile(TypedDict):
    id: int
    gameVersions: list[str]
    fileDate: str
    releaseType: NotRequired[int]
    isAvailable: NotRequired[bool]
    downloadUrl: NotRequired[str | None]


class CurseFileIndex(TypedDict):
    fileId: int
    gameVersion: str
    releaseType: int


class CurseProject(TypedDict):
    id: int
    slug: str
    latestFilesIndexes: NotRequired[list[CurseFileIndex]]


def parse_curse_file(value: JSON) -> CurseFile:
    record = json_dict(value)
    versions = json_list(record.get("gameVersions"))
    if not all(isinstance(version, str) for version in versions):
        raise ValueError("Field gameVersions: expected strings")
    parsed: CurseFile = {
        "id": field(record, "id", int),
        "gameVersions": [version for version in versions if isinstance(version, str)],
        "fileDate": field(record, "fileDate", str),
    }
    if "releaseType" in record:
        parsed["releaseType"] = field(record, "releaseType", int)
    if "isAvailable" in record:
        parsed["isAvailable"] = field(record, "isAvailable", bool)
    if "downloadUrl" in record:
        parsed["downloadUrl"] = (
            None if record["downloadUrl"] is None else field(record, "downloadUrl", str)
        )
    return parsed


def parse_curse_project(value: JSON) -> CurseProject:
    record = json_dict(value)
    parsed: CurseProject = {
        "id": field(record, "id", int),
        "slug": field(record, "slug", str),
    }
    if "latestFilesIndexes" in record:
        indexes: list[CurseFileIndex] = []
        for index_value in json_list(record["latestFilesIndexes"]):
            entry = json_dict(index_value)
            indexes.append(
                {
                    "fileId": field(entry, "fileId", int),
                    "gameVersion": field(entry, "gameVersion", str),
                    "releaseType": field(entry, "releaseType", int),
                }
            )
        parsed["latestFilesIndexes"] = indexes
    return parsed


def curse_candidate(current: CurseFile, files: Iterable[CurseFile]) -> CurseFile:
    versions = set(current["gameVersions"])
    if not versions:
        raise ValueError("Pinned CurseForge file has no game compatibility metadata")
    candidates = [
        file
        for file in files
        if file["id"] > current["id"]
        and file["fileDate"] > current["fileDate"]
        and file.get("releaseType") == 1
        and file.get("isAvailable", False)
        and versions.intersection(file["gameVersions"])
    ]
    return max(
        candidates, key=lambda file: (file["fileDate"], file["id"]), default=current
    )


def curse_latest(current: CurseFile, project: CurseProject) -> CurseFile:
    # Validate compatibility metadata before making any further requests.
    curse_candidate(current, [])
    base = f"https://api.curseforge.com/v1/mods/{project['id']}/files"
    file_ids = {
        entry["fileId"]
        for entry in project.get("latestFilesIndexes", [])
        if entry["gameVersion"] in current["gameVersions"] and entry["releaseType"] == 1
    }
    indexed: list[CurseFile] = []
    for file_id in sorted(file_ids):
        if file_id == current["id"]:
            indexed.append(current)
            continue

        result = json_dict(_api.request_json(f"{base}/{file_id}"))
        indexed.extend(_api.parsed_entries([result.get("data")], parse_curse_file))

    latest = curse_candidate(current, indexed)
    if latest["id"] != current["id"] or current["id"] in file_ids:
        return latest

    # Missing or unusable indexes require a history search, limited to the
    # pinned file's game versions rather than every variant of the addon.
    files = (
        file
        for version in sorted(set(current["gameVersions"]))
        for file in _api.parsed_entries(
            _api.pages(base + "?" + urlencode({"gameVersion": version}), curse=True),
            parse_curse_file,
        )
    )
    return curse_candidate(current, files)


def retrieve(url: str, homepage: str | None) -> str:
    """Find the newest stable file compatible with the pinned file."""
    match = re.fullmatch(
        r"https://www.curseforge.com/wow/addons/([^/]+)", homepage or ""
    )
    if match is None:
        raise ValueError(f"Unsupported CurseForge homepage: {homepage}")
    slug = match[1]
    file_match = re.search(r"/files/(\d+)/(\d+)/", url)
    if file_match is None:
        raise ValueError(f"Unsupported CurseForge source: {url}")
    projects = [
        project
        for project in _api.parsed_entries(
            _api.pages(
                "https://api.curseforge.com/v1/mods/search?"
                + urlencode({"gameId": 1, "slug": slug}),
                curse=True,
            ),
            parse_curse_project,
        )
        if project["slug"] == slug
    ]
    if len(projects) != 1:
        raise ValueError(f"Cannot identify CurseForge project {slug}")
    project = projects[0]
    file_id = int(file_match[1]) * 1000 + int(file_match[2])
    current = parse_curse_file(
        json_dict(
            _api.request_json(
                f"https://api.curseforge.com/v1/mods/{project['id']}/files/{file_id}"
            )
        ).get("data")
    )
    latest = curse_latest(current, project)
    candidate = url if latest["id"] == file_id else latest.get("downloadUrl")
    if not candidate:
        print(
            f"Warning: skipping {slug} file {latest['id']}: CurseForge returned no "
            "download URL; keeping pinned release",
            file=sys.stderr,
        )
        return url

    return candidate
