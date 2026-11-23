#!/usr/bin/env python3
"""Assemble the complete Skill from the pinned base plus ordered release overlays."""
from __future__ import annotations
import argparse, hashlib, json, shutil, zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXCLUDE_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}
SUPERSEDED_OVERLAYS = {"releases/3.4.2/": {"replaced_by": "releases/3.4.3/", "required_retained_files": ["scripts/ai_video_assets_v2_v342.py", "scripts/content_decision_gate_v342.py", "scripts/illustration_assets_v2_v342.py", "scripts/run_pipeline_v3_4.py", "scripts/test_v342_quality_gates.py", "scripts/test_v342_review_gates.py"]}}

def should_copy(rel: Path) -> bool:
    if any(p in EXCLUDE_PARTS for p in rel.parts): return False
    first = rel.parts[0] if rel.parts else ""
    return first in {"SKILL.md", "PACKAGE-METADATA.json", "INSTALL.md", "agents", "assets", "references", "samples", "scripts", "schemas", "tests"} or first.startswith("UPGRADE-")

def overlay_files(overlay: Path, version: str):
    for source in sorted(overlay.rglob("*")):
        if not source.is_file(): continue
        rel = source.relative_to(overlay)
        if any(p in EXCLUDE_PARTS for p in rel.parts): continue
        if rel.parts[:2] == ("skills", "spoken-script-engine"): dest_rel = Path(*rel.parts[2:])
        elif rel.parts and rel.parts[0] == "skills": continue
        elif rel.name == "README.md": dest_rel = Path("release-history") / f"{version}-README.md"
        else: dest_rel = rel
        if dest_rel.parts and should_copy(dest_rel): yield source, dest_rel

def assemble(repo: Path, output_dir: Path, zip_path: Path):
    registry = json.loads((repo / "REPO-REGISTRY.json").read_text(encoding="utf-8"))
    version = registry["version"]; base = repo / registry["base_path"]
    if not base.is_dir(): raise FileNotFoundError("Pinned base path missing: " + str(base))
    if output_dir.exists(): shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    for source in sorted(base.rglob("*")):
        if source.is_file():
            rel = source.relative_to(base)
            if should_copy(rel):
                target = output_dir / rel; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
    superseded = []
    for overlay_path in registry.get("overlay_paths", []):
        overlay = repo / overlay_path
        if not overlay.is_dir():
            policy = SUPERSEDED_OVERLAYS.get(overlay_path)
            if not policy: raise FileNotFoundError("Pinned overlay missing and not declared superseded: " + overlay_path)
            replacement = repo / policy["replaced_by"]
            missing = [name for name in policy["required_retained_files"] if not (replacement / name).is_file()]
            if missing: raise FileNotFoundError("Superseded overlay content not retained in " + policy["replaced_by"] + ": " + ", ".join(missing))
            superseded.append({"path": overlay_path, "replaced_by": policy["replaced_by"], "verified_retained_files": policy["required_retained_files"]})
            continue
        for source, rel in overlay_files(overlay, overlay.name):
            target = output_dir / rel; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
    metadata_path = output_dir / "PACKAGE-METADATA.json"
    if not metadata_path.is_file(): raise FileNotFoundError("Assembled package metadata missing")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if any(metadata.get(k) != version for k in ("skill_package_version", "skill_core_version", "skill_runtime_overlay_version")):
        raise ValueError("Assembled package version does not match REPO-REGISTRY")
    if version == "3.6.1" and not (output_dir / "scripts/run_pipeline_v3_6_1.py").is_file(): raise FileNotFoundError("v3.6.1 sole entrypoint missing")
    for required in ("SKILL.md", "references/acceptance-15-v361.md", "schemas/acceptance-15-v361.schema.json", "scripts/acceptance_contract_v361.py", "tests/test_acceptance_contract_v361.py"):
        if not (output_dir / required).is_file(): raise FileNotFoundError("Assembled package missing required file: " + required)
    manifest = {"package":"spoken-script-engine","version":version,"repository":registry.get("repository"),"asset_ref":registry.get("asset_ref"),"manifest_ref":registry.get("manifest_ref"),"registry_commit":registry.get("registry_commit"),"base_path":registry.get("base_path"),"overlay_paths":registry.get("overlay_paths",[]),"superseded_overlay_paths":superseded,"files":[]}
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "BUILD-MANIFEST.json": manifest["files"].append({"path":path.relative_to(output_dir).as_posix(),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"bytes":path.stat().st_size})
    (output_dir / "BUILD-MANIFEST.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if zip_path.exists(): zip_path.unlink()
    zip_path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(zip_path,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in sorted(output_dir.rglob("*")):
            if path.is_file(): z.write(path,Path("spoken-script-engine") / path.relative_to(output_dir))
    with zipfile.ZipFile(zip_path) as z:
        names=set(z.namelist())
        if "spoken-script-engine/SKILL.md" not in names or "spoken-script-engine/scripts/run_pipeline_v3_6_1.py" not in names: raise ValueError("ZIP round-trip verification failed")
    return {"version":version,"file_count":sum(1 for p in output_dir.rglob("*") if p.is_file()),"zip":str(zip_path),"zip_bytes":zip_path.stat().st_size}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--repo",default=str(REPO)); p.add_argument("--output-dir",default="dist/complete-skill"); p.add_argument("--zip",default="dist/spoken-script-engine-v3.6.1-skill.zip")
    a=p.parse_args(); repo=Path(a.repo).resolve()
    print(json.dumps(assemble(repo,repo/a.output_dir,repo/a.zip),ensure_ascii=False,indent=2))
if __name__=="__main__": main()
