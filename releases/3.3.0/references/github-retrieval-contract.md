# GitHub Retrieval Contract — 3.3.0

Repository: `wakazhangjiahuang/spoken-script-engine`.

1. Read `REPO-REGISTRY.json` first.
2. Use `asset_ref` for the active runtime overlay; use `manifest_ref` only for the separately pinned historical AI-video sample source where specified.
3. Read only the active overlay README, manifest, entrypoints, required schemas and task-matched references.
4. Record repository, refs, registry hash, loaded asset IDs, excluded asset IDs, file hashes and retrieval status.
5. Verify private plugin assets against their private manifest SHA; never upload private source files to the public repository.
6. Do not substitute unpinned `main` content for a pinned release.

If the repository, commit, manifest or file hash cannot be verified, mark KNOWLEDGE_NOT_VERIFIED and block release. Offline fallback is allowed only when the private bundle and every required SHA match the current pinned configuration; mark OFFLINE_PINNED_FALLBACK. Never silently fall back to a historical snapshot.
