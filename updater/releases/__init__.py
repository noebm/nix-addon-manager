"""Retrieve typed release candidates without exposing source-specific handling."""

from dataclasses import dataclass

from . import curseforge, github


@dataclass(frozen=True)
class Release:
    url: str
    version: str | None = None
    digest: str | None = None


class Retriever:
    """Share release metadata across components for a single update run."""

    def __init__(self) -> None:
        self._github_releases: dict[str, list[github.GitHubRelease]] = {}

    def retrieve(self, url: str, *, homepage: str | None = None) -> Release:
        if url.startswith("https://github.com/"):
            candidate, version, digest = github.retrieve(url, self._github_releases)
            return Release(candidate, version, digest)
        if url.startswith("https://edge.forgecdn.net/"):
            return Release(curseforge.retrieve(url, homepage))

        raise ValueError(f"Unsupported release source: {url}")
