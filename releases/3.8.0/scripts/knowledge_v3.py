"""Read immutable, SHA-256 verified spoken-script knowledge published in Git."""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import unicodedata
from urllib.parse import quote

REGISTRY = "registries/2026-11-27.1/KNOWLEDGE-REGISTRY.json"
LEGACY_REGISTRY = "KNOWLEDGE-REGISTRY.json"
COMMIT = re.compile(r"[a-f0-9]{40}")
DIGEST = re.compile(r"[a-f0-9]{64}")
PLATFORMS = {"xiaohongshu", "douyin", "channels", "shared"}
ARCHIVED = "historical_only"


def repo_path(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or str(path) != value or ":" in value or ".." in path.parts:
        raise ValueError(f"Invalid repository path: {value}")
    return value


def verify_digest(data: bytes, expected: str, path: str) -> None:
    if not DIGEST.fullmatch(expected) or sha256(data).hexdigest() != expected:
        raise ValueError(f"KB_HASH_MISMATCH: SHA-256 mismatch: {path}")


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
    def __init__(self, root: Path, registry_ref: str = "HEAD", *,
                 registry_path: str = REGISTRY, project_scopes=()):
        self.root = root.resolve(strict=True)
        if registry_ref != "HEAD" and not COMMIT.fullmatch(registry_ref):
            raise ValueError("Registry ref must be a commit SHA or checkout HEAD")
        pinned = self.git("rev-parse", "--verify", f"{registry_ref}^{{commit}}").decode().strip()
        self.load(pinned, registry_path, self.read_git_file, project_scopes=project_scopes)

    def read_git_file(self, ref: str, path: str) -> bytes:
        return self.git("show", f"{ref}:{repo_path(path)}")

    @classmethod
    def from_reader(cls, registry_ref, reader, registry_path=REGISTRY, *,
                    repository_id, repository, visibility, project_scopes=()):
        """Use an authenticated connector reader and independently fetched repository metadata."""
        instance = cls.__new__(cls)
        if visibility != "private":
            raise ValueError("KB_ACCESS_DENIED: expected a private repository")
        instance.load(registry_ref, registry_path, reader, repository_id=repository_id,
                      repository=repository, project_scopes=project_scopes)
        return instance

    def load(self, registry_ref, registry_path, reader, *, repository_id=None, repository=None,
             project_scopes=()):
        if not COMMIT.fullmatch(registry_ref):
            raise ValueError("KB_VERSION_MISMATCH: registry must be pinned to a commit")
        self.registry_ref = registry_ref
        self.reader = reader
        self.project_scopes = frozenset(project_scopes)
        self.registry = json.loads(reader(registry_ref, repo_path(registry_path)))
        if self.registry["schema_version"] != 1 or self.registry["visibility_required"] != "private":
            raise ValueError("KB_VERSION_MISMATCH: unsupported knowledge registry")
        if repository_id is not None and (str(repository_id) != self.registry.get("repository_id")
                or repository != self.registry["repository"]):
            raise ValueError("KB_ACCESS_DENIED: repository ID or owner differs")
        self.ref = self.registry["asset_ref"]
        if not COMMIT.fullmatch(self.ref):
            raise ValueError("KB_VERSION_MISMATCH: assets must be pinned to a commit")
        self.manifest = json.loads(self.checked(self.registry["manifest_path"], self.registry["manifest_sha256"]))
        if self.manifest["schema_version"] != 1 or self.manifest["version"] != self.registry["version"]:
            raise ValueError("KB_VERSION_MISMATCH: manifest and registry disagree")
        self.records = {}
        self.index = {}
        self.adapters = {}
        self.catalog = {}
        if "adapter_registry" in self.manifest:
            metadata = self.manifest["adapter_registry"]
            adapters = json.loads(self.checked(metadata["path"], metadata["sha256"]))["adapters"]
            self.adapters = {row["id"]: row for row in adapters}
            if len(self.adapters) != len(adapters):
                raise ValueError("KB_VERSION_MISMATCH: duplicate adapter IDs")
        if "catalog" in self.manifest:
            metadata = self.manifest["catalog"]
            self.catalog = json.loads(self.checked(metadata["path"], metadata["sha256"]))["records"]
        self.domains = {row["domain"] for row in self.adapters.values()}
        for asset in self.manifest["assets"]:
            path = asset["path"]
            if asset.get("project_scope") and asset["project_scope"] not in self.project_scopes:
                continue
            lines = self.checked(path, asset["sha256"]).splitlines()
            if len(lines) != asset["records"]:
                raise ValueError(f"Record count mismatch: {path}")
            for position, line in enumerate(lines, 1):
                item = json.loads(line)
                ident = item["id"]
                if ident in self.records:
                    raise ValueError(f"Duplicate knowledge ID: {ident}")
                metadata = self.catalog.get(ident, {})
                if self.catalog and (metadata.get("shard") != path or metadata.get("line") != position
                                     or metadata.get("project_scope") != asset.get("project_scope")
                                     or metadata.get("status") != item["status"]
                                     or metadata.get("domain") != item["domain"]):
                    raise ValueError(f"KB_VERSION_MISMATCH: invalid catalogue mapping for {ident}")
                self.domains.add(item["domain"])
                self.records[ident] = dict(item, classification=metadata, indexed_path=path, line=position)
                aliases = " ".join(metadata.get("aliases", []))
                self.index[ident] = (features(ident + " " + item["title"] + " " + aliases), features(item["text"]))
        if self.catalog and set(self.records) != {
                key for key, row in self.catalog.items()
                if not row.get("project_scope") or row["project_scope"] in self.project_scopes}:
            raise ValueError("KB_VERSION_MISMATCH: catalogue coverage differs from shards")

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
        data = self.reader(self.ref, repo_path(path))
        verify_digest(data, expected, path)
        return data

    def version(self) -> dict:
        return {
            "repository": self.registry["repository"],
            "version": self.manifest["version"],
            "registry_ref": self.registry_ref,
            "asset_ref": self.ref,
            "repository_id": self.registry.get("repository_id"),
            "manifest_sha256": self.registry["manifest_sha256"],
        }

    def status(self) -> dict:
        return {
            **self.version(),
            "counts_by_status": {status: sum(row["status"] == status for row in self.records.values())
                                 for status in sorted({row["status"] for row in self.records.values()})},
            "originals": sum(not row.get("project_scope") or row["project_scope"] in self.project_scopes
                             for row in self.manifest.get("originals", [])),
            "archives": [row for row in self.manifest.get("archives", [])
                         if not row.get("project_scope") or row["project_scope"] in self.project_scopes],
        }

    def summary(self, item: dict) -> dict:
        return {
            **{key: val for key, val in item.items() if key != "text"},
            "citation": f"https://github.com/{self.registry['repository']}/blob/{self.ref}/"
                        + quote(item["indexed_path"]) + f"#L{item['line']}",
        }

    def authorize(self, project_scope):
        if project_scope and project_scope not in self.project_scopes:
            raise ValueError("KB_ACCESS_DENIED: no authorized project scope")

    def search(self, query: str, platform: str = "", domain: str = "", kind: str = "",
               status: str = "", limit: int = 6, *, adapter_id: str = "", industry_tag: str = "",
               business_model: str = "", buyer_role: str = "", content_goal: str = "",
               project_scope: str = "") -> dict:
        self.authorize(project_scope)
        if platform and platform not in PLATFORMS:
            raise ValueError(f"Unknown platform: {platform}")
        if adapter_id:
            if adapter_id not in self.adapters:
                raise ValueError(f"Unknown adapter: {adapter_id}")
            adapter_domain = self.adapters[adapter_id]["domain"]
            if domain and domain != adapter_domain:
                raise ValueError("Adapter and domain disagree")
            domain = adapter_domain
        if domain and domain not in self.domains:
            raise ValueError(f"Unknown domain: {domain}")
        if self.adapters and not domain:
            domain = "shared"
        if len(query) > 500 or not 1 <= limit <= 15:
            raise ValueError("Query limit is 500 characters and 1–15 results")
        filters = {"industry_tags": industry_tag, "business_models": business_model,
                   "buyer_roles": buyer_role, "content_goals": content_goal}
        q = normalize(query).strip()
        tokens = features(q)
        hits = []
        for ident, item in self.records.items():
            metadata = item["classification"]
            if metadata.get("project_scope", "") != project_scope:
                continue
            if platform and item["platform"] != platform:
                continue
            if domain and item["domain"] != domain:
                continue
            if adapter_id and metadata.get("adapter_id") != adapter_id:
                continue
            if any(value and value not in metadata.get(key, []) for key, value in filters.items()):
                continue
            if kind and item["kind"] != kind:
                continue
            if status and item["status"] != status:
                continue
            if item["status"] == ARCHIVED and not (status == ARCHIVED or kind == "archive"):
                continue
            if metadata and not (status or kind) and item["status"] != "current_guidance":
                continue
            title, body = self.index[ident]
            score = 5 * len(tokens & title) + len(tokens & body)
            if q and (q == normalize(ident) or q in normalize(item["title"])):
                score += 50
            if q and not score:
                continue
            hits.append((score, ident))
        hits.sort(key=lambda match: (-match[0], match[1]))
        return {**self.version(), "retrieval_status": "VERIFIED" if hits else "KB_NO_MATCH", "results": [
            dict(self.summary(self.records[ident]), excerpt=self.records[ident]["text"][:440])
            for _, ident in hits[:limit]
        ]}

    def read(self, asset_id: str, offset: int = 0, *, project_scope: str = "",
             include_history: bool = False) -> dict:
        self.authorize(project_scope)
        item = self.records.get(asset_id)
        if item is None or item["classification"].get("project_scope", "") != project_scope:
            raise ValueError("KB_NO_MATCH: unknown knowledge ID")
        if item["status"] == ARCHIVED and not include_history:
            raise ValueError("KB_NO_MATCH: explicit historical access required")
        text = item["text"]
        if not 0 <= offset <= len(text):
            raise ValueError("Offset outside the source text")
        end = offset + 5000
        return {**self.version(), **self.summary(item), "text": text[offset:end],
                "next_offset": end if end < len(text) else None}
