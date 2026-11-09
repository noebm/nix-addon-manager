"""Discover upstream releases and update pinned Nix addon sources explicitly."""

import argparse
import base64
import difflib
import fcntl
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import zipfile
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, NotRequired, TypedDict
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

SOURCE = re.compile(r'url = "([^"\n]+)";\s*hash = "(sha256-[^"\n]+)";')
VERSION = re.compile(r'(?m)^  version = "([^"\n]+)";')


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


class CurseFile(TypedDict):
    id: int
    gameVersions: list[str]
    fileDate: str
    releaseType: NotRequired[int]
    isAvailable: NotRequired[bool]
    downloadUrl: NotRequired[str | None]


def request_json(url: str) -> Any:
    headers = {"User-Agent": "nix-addon-manager-updater", "Accept": "application/json"}
    if urlparse(url).hostname == "api.curseforge.com":
        key = os.environ.get("CURSEFORGE_API_KEY")
        if not key:
            raise ValueError("CurseForge updates require CURSEFORGE_API_KEY")
        headers["x-api-key"] = key
    elif urlparse(url).hostname == "api.github.com" and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]

    print(f"Fetching release metadata: {url}", file=sys.stderr, flush=True)
    with urlopen(Request(url, headers=headers), timeout=60) as response:
        return json.load(response)


def pages(url: str, *, curse: bool = False) -> Iterator[dict[str, Any]]:
    page_size = 50 if curse else 100

    if curse:

        def query(page: int) -> dict[str, int]:
            return {"pageSize": page_size, "index": page * page_size}

        def response(result):
            return result["data"]
    else:

        def query(page: int) -> dict[str, int]:
            return {"per_page": page_size, "page": page + 1}

        def response(result):
            return result

    page = 0

    while True:
        result = request_json(
            url + ("&" if "?" in url else "?") + urlencode(query(page))
        )
        values = response(result)
        yield from values
        if len(values) < page_size:
            return
        page += 1


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


def curse_candidate(current: CurseFile, files: Iterable[CurseFile]) -> CurseFile:
    versions = set(current["gameVersions"])
    if not versions:
        raise ValueError("Pinned CurseForge file has no game compatibility metadata")
    candidates = [
        file
        for file in files
        if file["id"] > current["id"]
        and file["fileDate"] > current["fileDate"]
        and file["releaseType"] == 1
        and file["isAvailable"]
        and versions.intersection(file["gameVersions"])
    ]
    return max(
        candidates, key=lambda file: (file["fileDate"], file["id"]), default=current
    )


def curse_latest(current: CurseFile, project: dict[str, Any]) -> CurseFile:
    # Validate compatibility metadata before making any further requests.
    curse_candidate(current, [])
    base = f"https://api.curseforge.com/v1/mods/{project['id']}/files"
    file_ids = {
        entry["fileId"]
        for entry in project.get("latestFilesIndexes", [])
        if entry["gameVersion"] in current["gameVersions"] and entry["releaseType"] == 1
    }
    indexed = [
        current
        if file_id == current["id"]
        else request_json(f"{base}/{file_id}")["data"]
        for file_id in sorted(file_ids)
    ]
    latest = curse_candidate(current, indexed)
    if latest["id"] != current["id"] or current["id"] in file_ids:
        return latest

    # Missing or unusable indexes require a history search, limited to the
    # pinned file's game versions rather than every variant of the addon.
    files = (
        file
        for version in sorted(set(current["gameVersions"]))
        for file in pages(base + "?" + urlencode({"gameVersion": version}), curse=True)
    )
    return curse_candidate(current, files)


class RangeUnsupported(Exception):
    """The server cannot provide a consistent seekable byte stream."""


class RemoteZip(io.RawIOBase):
    """Seekable HTTP reader for ZIP directory and TOC discovery."""

    def __init__(self, url):
        super().__init__()
        if urlparse(url).scheme != "https":
            raise ValueError("Release downloads must use HTTPS")
        self.url = url
        self.position = 0
        self.size = None
        self.validator = None
        self._range(0, 0)

    def _range(self, start, end):
        headers = {
            "User-Agent": "nix-addon-manager-updater",
            "Range": f"bytes={start}-{end}",
            "Accept-Encoding": "identity",
        }
        if self.validator:
            headers["If-Range"] = self.validator

        try:
            with urlopen(Request(self.url, headers=headers), timeout=60) as response:
                if urlparse(response.url).scheme != "https":
                    raise ValueError("Release download redirected away from HTTPS")
                match = re.fullmatch(
                    r"bytes (\d+)-(\d+)/(\d+)",
                    response.headers.get("Content-Range", ""),
                )
                if response.status != 206 or not match:
                    raise RangeUnsupported()
                first, last, size = map(int, match.groups())
                if (
                    first != start
                    or last != min(end, size - 1)
                    or (self.size is not None and size != self.size)
                ):
                    raise RangeUnsupported()
                validator = response.headers.get("ETag") or response.headers.get(
                    "Last-Modified"
                )
                if self.validator and validator != self.validator:
                    raise RangeUnsupported()
                self.size = size
                self.validator = validator
                data = response.read(last - first + 2)
                if len(data) != last - first + 1:
                    raise RangeUnsupported()
                return data
        except HTTPError as error:
            if error.code in (400, 405, 416, 501):
                error.close()
                raise RangeUnsupported() from error
            raise

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        position = offset + (
            self.position if whence == 1 else self.size if whence == 2 else 0
        )
        if whence not in (0, 1, 2) or position < 0:
            raise ValueError("Invalid ZIP seek")
        self.position = position
        return position

    def read(self, size=-1):
        end = self.size if size < 0 else min(self.size, self.position + size)
        if end <= self.position:
            return b""
        data = self._range(self.position, end - 1)
        self.position = end
        return data


def discover_directories(
    url: str, interface: int | None
) -> tuple[set[str], str | None]:
    """Read ZIP paths and TOCs through ranges, falling back when unsupported.

    Discovery is not full archive validation or cryptographic verification.
    """
    try:
        with RemoteZip(url) as source:
            return validate_archive(source, interface, check_crc=False)
    except RangeUnsupported:
        _, directories, version = download(url, interface)
        return directories, version


def directory_declaration(directories: Iterable[str]) -> str:
    """Render a deterministic pinned directory declaration."""
    return (
        "addonDirectories = [\n"
        + "".join(f"      {nix_string(name)}\n" for name in sorted(directories))
        + "    ];"
    )


def validate_archive(
    source: BinaryIO | io.RawIOBase,
    interface: int | None,
    *,
    check_crc: bool = True,
) -> tuple[set[str], str | None]:
    directories = set()
    versions = []
    toc_count = 0
    with zipfile.ZipFile(source) as archive:
        for entry in archive.infolist():
            name = entry.filename.replace("\\", "/")
            path = PurePosixPath(name)
            mode = entry.external_attr >> 16
            if (
                path.is_absolute()
                or ".." in path.parts
                or not path.parts
                or ":" in path.parts[0]
                or "\x00" in name
                or stat.S_ISLNK(mode)
                or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)
            ):
                raise ValueError(f"Unsafe archive entry: {name}")
            if not name.endswith("/") and len(path.parts) < 2:
                raise ValueError(f"File outside addon directory: {name}")
            directories.add(path.parts[0])
            if name.lower().endswith(".toc") and len(path.parts) == 2:
                toc_count += 1
                content = archive.read(entry).decode("utf-8-sig", errors="replace")
                interfaces = re.findall(
                    r"^##\s*Interface\s*:\s*(.+)$",
                    content,
                    re.MULTILINE | re.IGNORECASE,
                )
                if interface is not None and not any(
                    str(interface) in re.findall(r"\d+", value) for value in interfaces
                ):
                    raise ValueError(
                        f"Incompatible or missing Interface in {name}; expected {interface}"
                    )
                version = re.search(
                    r"^##\s*Version\s*:\s*(.+)$", content, re.MULTILINE | re.IGNORECASE
                )
                if version:
                    versions.append(version[1].strip())
        bad = archive.testzip() if check_crc else None
        if bad:
            raise ValueError(f"Corrupt archive entry: {bad}")
    if not directories or not toc_count:
        raise ValueError("Archive contains no addon TOC files")
    return directories, versions[0] if versions else None


def download(url: str, interface: int | None) -> tuple[str, set[str], str | None]:
    if urlparse(url).scheme != "https":
        raise ValueError("Release downloads must use HTTPS")
    print(f"Downloading: {url}", file=sys.stderr, flush=True)
    digest = hashlib.sha256()
    with tempfile.TemporaryFile() as archive:
        with urlopen(
            Request(url, headers={"User-Agent": "nix-addon-manager-updater"}),
            timeout=60,
        ) as response:
            if urlparse(response.url).scheme != "https":
                raise ValueError("Release download redirected away from HTTPS")
            total = response.headers.get("Content-Length")
            total = int(total) if total and total.isdigit() else None
            transferred = 0
            started = last_report = time.monotonic()
            if total is not None:
                print(
                    f"  Archive size: {total / 1024**2:.1f} MiB",
                    file=sys.stderr,
                    flush=True,
                )
            while chunk := response.read(64 * 1024):
                digest.update(chunk)
                archive.write(chunk)
                transferred += len(chunk)
                now = time.monotonic()
                if now - last_report >= 5:
                    size = f"{transferred / 1024**2:.1f} MiB"
                    if total:
                        size += (
                            f" / {total / 1024**2:.1f} MiB ({transferred / total:.0%})"
                        )
                    speed = transferred / 1024**2 / max(now - started, 0.001)
                    print(
                        f"  Downloaded {size}, {speed:.2f} MiB/s",
                        file=sys.stderr,
                        flush=True,
                    )
                    last_report = now
            elapsed = time.monotonic() - started
            print(
                f"  Download complete: {transferred / 1024**2:.1f} MiB in {elapsed:.1f}s",
                file=sys.stderr,
                flush=True,
            )
        print(
            "  Validating archive (paths, TOCs, and CRC checks)...",
            file=sys.stderr,
            flush=True,
        )
        archive.seek(0)
        directories, version = validate_archive(archive, interface)
        print("  Archive validated", file=sys.stderr, flush=True)
    return "sha256-" + base64.b64encode(digest.digest()).decode(), directories, version


@dataclass
class PendingValidation:
    url: str
    digest: str
    interface: int | None
    directories: set[str]


def propose(
    name: str,
    text: str,
    github_releases: dict[str, list[GitHubRelease]] | None = None,
) -> tuple[str, list[PendingValidation]]:
    pending_validation: list[PendingValidation] = []
    sources = list(SOURCE.finditer(text))
    directory_block = re.search(r"addonDirectories = \[(.*?)\];", text, re.DOTALL)
    if not sources or not directory_block or len(VERSION.findall(text)) != 1:
        raise ValueError(f"Unsupported package definition: {name}")
    expected = set(re.findall(r'"([^"\n]+)"', directory_block[1]))
    compatibility = re.search(r"interface = (\d+);", text)
    interface = int(compatibility[1]) if compatibility else None
    replacements = []
    directories = set()
    changed = False
    package_version = VERSION.search(text)[1]
    if github_releases is None:
        github_releases = {}

    candidates = []
    digests = {}
    for index, source in enumerate(sources):
        url, old_hash = source.groups()
        new_version = None
        if url.startswith("https://github.com/"):
            repository = "/".join(url.split("/")[3:5])
            # All current multi-source packages use one upstream repository.
            if repository not in github_releases:
                github_releases[repository] = list(
                    pages(f"https://api.github.com/repos/{repository}/releases")
                )
            candidate, new_version = github_candidate(url, github_releases[repository])
            assets = [
                asset
                for release in github_releases[repository]
                for asset in release["assets"]
                if asset["browser_download_url"] == candidate
            ]
            digest = assets[0].get("digest") if len(assets) == 1 else None
            if digest:
                if not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest):
                    raise ValueError(f"Invalid GitHub asset digest: {candidate}")
                digests[candidate] = (
                    "sha256-" + base64.b64encode(bytes.fromhex(digest[7:])).decode()
                )

        elif url.startswith("https://edge.forgecdn.net/"):
            homepage = re.search(
                r'homepage = "https://www.curseforge.com/wow/addons/([^"/]+)";', text
            )
            file_match = re.search(r"/files/(\d+)/(\d+)/", url)
            if homepage is None or file_match is None:
                raise ValueError(f"Unsupported CurseForge source in {name}")
            projects = pages(
                "https://api.curseforge.com/v1/mods/search?"
                + urlencode({"gameId": 1, "slug": homepage[1]}),
                curse=True,
            )
            projects = [
                project for project in projects if project["slug"] == homepage[1]
            ]
            if len(projects) != 1:
                raise ValueError(f"Cannot identify CurseForge project {homepage[1]}")
            project = projects[0]
            file_id = int(file_match[1]) * 1000 + int(file_match[2])
            current = request_json(
                f"https://api.curseforge.com/v1/mods/{project['id']}/files/{file_id}"
            )["data"]
            latest = curse_latest(current, project)
            candidate = url if latest["id"] == file_id else latest.get("downloadUrl")
            if not candidate:
                raise ValueError(f"Upstream does not permit downloading {name}")
        else:
            raise ValueError(f"Unsupported release source: {url}")

        changed |= candidate != url
        candidates.append((source, candidate, new_version))
    if not changed:
        return text, pending_validation

    for index, (source, candidate, new_version) in enumerate(candidates):
        url, old_hash = source.groups()
        # Validate unchanged components too: the combined directory set must still
        # match the package declaration before publishing updated pins.
        print(f"Checking {name}: {candidate}", flush=True)
        if candidate in digests:
            new_hash = digests[candidate]
            component_directories, toc_version = discover_directories(
                candidate, interface
            )
            pending_validation.append(
                PendingValidation(
                    url=candidate,
                    digest=new_hash,
                    interface=interface,
                    directories=component_directories,
                )
            )
        else:
            new_hash, component_directories, toc_version = download(
                candidate, interface
            )
        if candidate == url and new_hash != old_hash:
            raise ValueError(f"Pinned archive changed upstream: {url}")
        if directories.intersection(component_directories):
            raise ValueError(f"Conflicting component directories in {name}")
        directories.update(component_directories)
        if index == 0 and candidate != url:
            package_version = new_version or toc_version
            if not package_version:
                raise ValueError(f"Missing package version in {name}")
        replacements.append(
            (
                source.start(),
                source.end(),
                f"url = {nix_string(candidate)};\n      hash = {nix_string(new_hash)};",
            )
        )
    if directories != expected:
        replacements.append(
            (
                directory_block.start(),
                directory_block.end(),
                directory_declaration(directories),
            )
        )
    for start, end, replacement in sorted(replacements, reverse=True):
        text = text[:start] + replacement + text[end:]
    proposal = VERSION.sub(
        lambda match: f"  version = {nix_string(package_version)};", text
    )
    return proposal, pending_validation


def nix_string(value: str) -> str:
    return json.dumps(value).replace("${", "\\${")


def update(repository: Path, names: list[str], *, apply: bool = False) -> None:
    originals = {}
    proposals = {}
    build_names = set()
    github_releases = {}
    pending_validation = []

    for name in dict.fromkeys(names):
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
            raise ValueError(f"Invalid addon name: {name}")
        package = repository / "addons" / name / "package.nix"
        components = sorted(package.parent.glob("components/*/package.nix"))
        for path in components or [package]:
            label = f"{name}/{path.parent.name}" if components else name
            original = path.read_text()
            proposal, validations = propose(label, original, github_releases)
            pending_validation.extend(validations)

            if proposal != original:
                relative = path.relative_to(repository)
                originals[relative] = original
                proposals[relative] = proposal
                build_names.add(name)
                print(
                    "".join(
                        difflib.unified_diff(
                            original.splitlines(True),
                            proposal.splitlines(True),
                            fromfile=str(path),
                            tofile=str(path),
                        )
                    ),
                    end="",
                )
    if not proposals:
        print("All selected addons are up to date")
        return
    if not apply:
        print("Preview only; pass --apply to build and write pins")
        return

    for validation in pending_validation:
        result = subprocess.run(
            [
                "nix",
                "store",
                "prefetch-file",
                "--json",
                "--expected-hash",
                validation.digest,
                validation.url,
            ],
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        archive = Path(json.loads(result.stdout)["storePath"])
        with archive.open("rb") as source:
            directories, _ = validate_archive(source, validation.interface)
        if directories != validation.directories:
            raise ValueError(
                f"Addon directories changed: expected {sorted(validation.directories)}, got {sorted(directories)}"
            )

    with tempfile.TemporaryDirectory(prefix="nix-addon-update-") as directory:
        staged = Path(directory) / "repository"
        shutil.copytree(
            repository,
            staged,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "result", "result-*"),
        )
        for relative, proposal in proposals.items():
            (staged / relative).write_text(proposal)
        subprocess.run(
            [
                "nix",
                "build",
                "--no-link",
                "--no-write-lock-file",
                *[f"path:{staged}#{name}" for name in sorted(build_names)],
            ],
            check=True,
        )

    for relative, original in originals.items():
        if (repository / relative).read_text() != original:
            raise ValueError(
                f"Package {relative} changed during validation; run the updater again"
            )
    for relative, proposal in proposals.items():
        path = repository / relative
        with tempfile.NamedTemporaryFile(
            mode="w", dir=path.parent, delete=False
        ) as output:
            temporary = Path(output.name)
            try:
                output.write(proposal)
                output.flush()
                os.fsync(output.fileno())
                os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
    print(
        "Pins updated; review the diff, then run the installer to apply them to the game"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--addon",
        action="append",
        help="Addon to update; repeat to select several (default: all)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Build updated packages and write validated pins",
    )
    args = parser.parse_args()
    try:
        repository = Path.cwd()
        # Lock the checkout directory itself, without creating repository files.
        lock = os.open(repository, os.O_RDONLY)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            names: list[str] = args.addon or sorted(
                path.parent.name
                for path in (repository / "addons").glob("*/package.nix")
            )
            if not names:
                raise ValueError("No addon packages found")
            update(repository, names, apply=args.apply)
        finally:
            os.close(lock)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        zipfile.BadZipFile,
        subprocess.CalledProcessError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
