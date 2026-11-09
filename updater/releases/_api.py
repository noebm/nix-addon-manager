"""JSON transport, pagination, and checked metadata parsing."""

import json
import os
import sys
from collections.abc import Callable, Iterable, Iterator
from typing import cast
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

type JSON = None | bool | int | float | str | list[JSON] | dict[str, JSON]


def json_dict(value: JSON) -> dict[str, JSON]:
    if not isinstance(value, dict):
        raise TypeError("Expected JSON object")
    return value


def json_list(value: JSON) -> list[JSON]:
    if not isinstance(value, list):
        raise TypeError("Expected JSON array")
    return value


def field[T](value: dict[str, JSON], name: str, kind: type[T]) -> T:
    result = value.get(name)
    if not isinstance(result, kind) or (kind is int and isinstance(result, bool)):
        raise ValueError(f"Field {name}: expected {kind.__name__}")
    return result


def parsed_entries[T](
    values: Iterable[JSON], parse: Callable[[JSON], T]
) -> Iterator[T]:
    for index, value in enumerate(values):
        try:
            entry = parse(value)
        except (TypeError, ValueError) as error:
            print(
                f"Warning: ignoring release metadata entry {index}: {error}",
                file=sys.stderr,
            )
            continue
        yield entry


def request_json(url: str) -> JSON:
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
        return cast(JSON, json.load(response))


def pages(url: str, *, curse: bool = False) -> Iterator[JSON]:
    page_size = 50 if curse else 100

    if curse:

        def query(page: int) -> dict[str, int]:
            return {"pageSize": page_size, "index": page * page_size}

        def response(result: JSON) -> list[JSON]:
            return json_list(json_dict(result).get("data"))
    else:

        def query(page: int) -> dict[str, int]:
            return {"per_page": page_size, "page": page + 1}

        def response(result: JSON) -> list[JSON]:
            return json_list(result)

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
