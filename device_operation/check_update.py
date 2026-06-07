from __future__ import annotations

import json
import logging
import re
import sys
import tomllib
import urllib.error
import urllib.request
import urllib.parse
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any, Callable


GITHUB_REPO = "Einzieg/Nova-AutoScript"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"
GITHUB_LATEST_RELEASE_API = f"{GITHUB_API_BASE}/releases/latest"
FALLBACK_VERSION = "0.1.0"

REQUEST_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Nova-AutoScript-Updater",
}
DOWNLOAD_HEADERS = {
    "Accept": "application/octet-stream",
    "User-Agent": "Nova-AutoScript-Updater",
}

ProgressCallback = Callable[[int, int], None]


class UpdateCheckError(RuntimeError):
    """Raised when GitHub release metadata cannot be fetched or parsed."""


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    download_url: str
    size: int = 0
    content_type: str = ""


@dataclass(frozen=True)
class UpdateInfo:
    current_version: str
    latest_version: str
    release_name: str
    release_url: str
    body: str
    asset: ReleaseAsset | None
    is_update_available: bool


def _candidate_pyproject_paths() -> list[Path]:
    candidates: list[Path] = []

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "pyproject.toml")

    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "pyproject.toml")

    candidates.append(Path.cwd() / "pyproject.toml")
    candidates.extend(parent / "pyproject.toml" for parent in Path(__file__).resolve().parents)

    result: list[Path] = []
    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved not in seen:
            result.append(path)
            seen.add(resolved)
    return result


def get_current_version() -> str:
    for path in _candidate_pyproject_paths():
        if not path.exists():
            continue
        with path.open("rb") as file:
            project = tomllib.load(file).get("project", {})
        version = project.get("version")
        if isinstance(version, str) and version:
            return version

    try:
        return metadata.version("novaah")
    except metadata.PackageNotFoundError:
        return FALLBACK_VERSION


def _version_parts(version: str) -> tuple[tuple[int, ...], str]:
    normalized = version.strip().lstrip("vV").split("+", 1)[0]
    main, _, suffix = normalized.partition("-")
    numbers = tuple(int(part) for part in re.findall(r"\d+", main))
    return numbers or (0,), suffix


def is_newer_version(latest: str, current: str) -> bool:
    latest_numbers, latest_suffix = _version_parts(latest)
    current_numbers, current_suffix = _version_parts(current)

    length = max(len(latest_numbers), len(current_numbers))
    latest_numbers += (0,) * (length - len(latest_numbers))
    current_numbers += (0,) * (length - len(current_numbers))

    if latest_numbers != current_numbers:
        return latest_numbers > current_numbers

    # Prefer a stable release over the same numeric prerelease.
    return bool(current_suffix and not latest_suffix)


def _safe_filename(filename: str) -> str:
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", filename).strip()
    return safe or "Nova-AutoScript-update.zip"


def _asset_score(asset: dict[str, Any]) -> int:
    name = str(asset.get("name") or "").lower()
    score = 0
    if name.endswith(".zip"):
        score += 20
    if "windows" in name or "win" in name:
        score += 10
    if "nova-auto" in name or "novaautoscript" in name:
        score += 5
    return score


def _select_asset(assets: list[dict[str, Any]]) -> ReleaseAsset | None:
    if not assets:
        return None

    asset = max(assets, key=_asset_score)
    download_url = asset.get("browser_download_url")
    if not download_url:
        return None

    return ReleaseAsset(
        name=str(asset.get("name") or "Nova-AutoScript-update.zip"),
        download_url=str(download_url),
        size=int(asset.get("size") or 0),
        content_type=str(asset.get("content_type") or ""),
    )


def default_download_dir() -> Path:
    return Path.home() / "Downloads" / "Nova-AutoScript"


class CheckUpdate:
    def __init__(
        self,
        current_version: str | None = None,
        *,
        api_url: str = GITHUB_LATEST_RELEASE_API,
        releases_url: str = GITHUB_RELEASES_URL,
        timeout: float = 10.0,
    ):
        self.current_version = current_version or get_current_version()
        self.api_url = api_url
        self.releases_url = releases_url
        self.timeout = timeout

    def _open_json(self, url: str) -> dict[str, Any]:
        request = urllib.request.Request(url, headers=REQUEST_HEADERS)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise UpdateCheckError(f"GitHub API 请求失败: HTTP {error.code} {detail}") from error
        except urllib.error.URLError as error:
            raise UpdateCheckError(f"无法连接 GitHub Releases: {error.reason}") from error

        try:
            data = json.loads(payload)
        except json.JSONDecodeError as error:
            raise UpdateCheckError("GitHub Releases 返回内容不是有效 JSON") from error

        if not isinstance(data, dict):
            raise UpdateCheckError("GitHub Releases 返回内容格式不正确")
        return data

    def _read_tag_or_commit_message(self, tag_name: str) -> str:
        tag_path = urllib.parse.quote(tag_name, safe="/")
        try:
            tag_ref = self._open_json(f"{GITHUB_API_BASE}/git/ref/tags/{tag_path}")
            tag_object = tag_ref.get("object") or {}
            object_type = tag_object.get("type")
            object_url = tag_object.get("url")
            object_sha = tag_object.get("sha")

            if object_type == "tag" and object_url:
                tag_data = self._open_json(str(object_url))
                return str(tag_data.get("message") or "").strip()

            if object_type == "commit" and object_sha:
                commit = self._open_json(f"{GITHUB_API_BASE}/commits/{object_sha}")
                commit_data = commit.get("commit") or {}
                return str(commit_data.get("message") or "").strip()
        except UpdateCheckError as error:
            # Release body is the primary source. Missing fallback text should not fail update checks.
            logging.warning(f"读取 tag/commit 更新内容失败: {error}")

        return ""

    def check_update(self) -> UpdateInfo:
        release = self._open_json(self.api_url)
        latest_version = str(release.get("tag_name") or "").strip()
        if not latest_version:
            raise UpdateCheckError("GitHub Release 缺少 tag_name")

        assets = release.get("assets") or []
        asset = _select_asset(assets if isinstance(assets, list) else [])
        release_url = str(release.get("html_url") or self.releases_url)
        body = str(release.get("body") or "").strip()
        if not body:
            body = self._read_tag_or_commit_message(latest_version)

        return UpdateInfo(
            current_version=self.current_version,
            latest_version=latest_version,
            release_name=str(release.get("name") or latest_version),
            release_url=release_url,
            body=body,
            asset=asset,
            is_update_available=is_newer_version(latest_version, self.current_version),
        )

    def download_asset(
        self,
        asset: ReleaseAsset,
        target_dir: Path | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> Path:
        target_dir = target_dir or default_download_dir()
        target_dir.mkdir(parents=True, exist_ok=True)

        destination = target_dir / _safe_filename(asset.name)
        temp_path = destination.with_name(f"{destination.name}.part")

        request = urllib.request.Request(asset.download_url, headers=DOWNLOAD_HEADERS)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                total = int(response.headers.get("Content-Length") or asset.size or 0)
                downloaded = 0
                if progress_callback:
                    progress_callback(downloaded, total)
                with temp_path.open("wb") as file:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        file.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total)
        except (urllib.error.URLError, OSError) as error:
            if temp_path.exists():
                temp_path.unlink()
            raise UpdateCheckError(f"下载更新包失败: {error}") from error

        temp_path.replace(destination)
        return destination
