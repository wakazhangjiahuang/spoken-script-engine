"""Read immutable, SHA-256 verified spoken-script knowledge published in Git."""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import unicodedata

REGISTRY = "KNOWLEDGE-REGISTRY.json"
COMMIT = re.compile(r"[a-f0-9]{40}")
DIGEST = re.compile(r"[a-f0-9]{64}")
PLATFORMS = {"xiaohongshu", "douyin", "channels", "shared"}
DOMAINS = {"ai_video", "illustration", "shared"}
ARCHIVED = "historical_only"


def repo_path(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or str(path) != value or ":" in value or ".." in path.parts:
        raise ValueError(f"Invalid repository path: {value}")
    return value


def verify_digest(data: bytes, expected: str, path: str) -> None:
    if not DIGEST.fullmatch(expected) or sha256(data).hexdigest() != expected:
        raise ValueError(f"SHA-256 mismatch: {path}")


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def features(text: str) -> set[str]:
    text = normalize(text)
    tokens = set(re.findall(r"[a-z0-9][a-z0-9_-]*", text))
    for run in re.findall(r"[\u3400-\u9fff]+", text):
        for size in (2, 3):
            tokens.update(run[i:i + size] for i in range(len(run) - size + 1))
    return tokens


class Snapshot:
    def __init__(self, root: Path, registry_ref: str = "HEAD"):
        self.root = root.resolve(strict=True)
        if registry_ref != "HEAD" and not COMMIT.fullmatch(registry_ref):
            raise ValueError("Registry ref must be a commit SHA or checkout HEAD")
        self.registry_ref = self.git("rev-parse", "--verify", f"{registry_ref}^{{commit}}").decode().strip()
        self.registry = json.loads(self.git("show", f"{self.registry_ref}:{REGISTRY}"))
        if self.registry["schema_version"] != 1 or self.registry["visibility_required"] != "private":
            raise ValueError("Unsupported knowledge registry")
        self.ref = self.registry["asset_ref"]
        if not COMMIT.fullmatch(self.ref):
            raise ValueError("Knowledge assets must be pinned to a commit")
        manifest_path = self.registry["manifest_path"]
        self.manifest = json.loads(self.checked(manifest_path, self.registry["manifest_sha256"]))
        if self.manifest["schema_version"] != 1 or self.manifest["version"] != self.registry["version"]:
            raise ValueError("Knowledge manifest version mismatch")
        self.records: dict[str, dict] = {}
        self.index: dict[str, tuple[set[str], set[str]]] = {}
        for asset in self.manifest["assets"]:
            path = asset["path"]
            lines = self.checked(path, asset["sha256"]).splitlines()
            if len(lines) != asset["records"]:
                raise ValueError(f"Record count mismatch: {path}")
            for line in lines:
                item = json.loads(line)
                ident = item["id"]
                if ident in self.records:
                    raise ValueError(f"Duplicate knowledge ID: {ident}")
                self.records[ident] = dict(item, indexed_path=path)
                self.index[ident] = (features(ident + " " + item["title"]), features(item["text"]))

    def git(self, *args: str) -> bytes:
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        result = subprocess.run(
            ["git", "-C", str(self.root), *args],
            check=False, capture_output=True, timeout=20, env=env,
        )
        if result.returncode:
            raise ValueError(f"Knowledge checkout could not serve {args[0]}")
        return result.stdout

    def checked(self, path: str, expected: str) -> bytes:
        data = self.git("show", f"{self.ref}:{repo_path(path)}")
        verify_digest(data, expected, path)
        return data

    def version(self) -> dict:
        return {
            "repository": self.registry["repository"],
            "version": self.manifest["version"],
            "registry_ref": self.registry_ref,
            "asset_ref": self.ref,
        }

    def status(self) -> dict:
        return {
            **self.version(),
            "counts_by_status": self.manifest["counts_by_status"],
            "originals": len(self.manifest["originals"]),
            "archives": self.manifest["archives"],
        }

    def summary(self, item: dict) -> dict:
        return {
            **{key: val for key, val in item.items() if key != "text"},
            "citation": f"https://github.com/{self.registry['repository']}/blob/{self.ref}/{item['indexed_path']}",
        }

    def search(self, query: str, platform: str = "", domain: str = "", kind: str = "",
               status: str = "", limit: int = 6) -> dict:
        if platform and platform not in PLATFORMS:
            raise ValueError(f"Unknown platform: {platform}")
        if domain and domain not in DOMAINS:
            raise ValueError(f"Unknown domain: {domain}")
        if len(query) > 500 or not 1 <= limit <= 15:
            raise ValueError("Query limit is 500 characters and 1–15 results")
        q = normalize(query).strip()
        tokens = features(q)
        hits = []
        for ident, item in self.records.items():
            if platform and item["platform"] != platform:
                continue
            if domain and item["domain"] != domain:
                continue
            if kind and item["kind"] != kind:
                continue
            if status and item["status"] != status:
                continue
            if item["status"] == ARCHIVED and not (status == ARCHIVED or kind == "archive"):
                continue
            title, body = self.index[ident]
            score = 5 * len(tokens & title) + len(tokens & body)
            if q and (q == normalize(ident) or q in normalize(item["title"])):
                score += 50
            if q and not score:
                continue
            hits.append((score, ident))
        hits.sort(key=lambda match: (-match[0], match[1]))
        return {**self.version(), "results": [
            dict(self.summary(self.records[ident]), excerpt=self.records[ident]["text"][:440])
            for _, ident in hits[:limit]
        ]}

    def read(self, asset_id: str, offset: int = 0) -> dict:
        if asset_id not in self.records:
            raise ValueError("Unknown knowledge ID")
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        item = self.records[asset_id]
        text = item["text"]
        end = offset + 5000
        return {**self.version(), **self.summary(item), "text": text[offset:end],
                "next_offset": end if end < len(text) else None}
