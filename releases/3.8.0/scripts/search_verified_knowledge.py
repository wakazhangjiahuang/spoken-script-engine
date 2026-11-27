"""Search authenticated GitHub files cached as CACHE/<full-commit>/<repository-path>."""
import argparse
import json
from pathlib import Path

from knowledge_v3 import Snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("status", "search", "read"))
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--query", default="")
    parser.add_argument("--id")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--include-history", action="store_true")
    for key in ("domain", "platform", "kind", "status", "adapter-id", "industry-tag",
                "business-model", "buyer-role", "content-goal"):
        parser.add_argument("--" + key, default="")
    args = parser.parse_args()
    config = json.loads((Path(__file__).resolve().parents[1] / "assets/connection-config.json").read_text())
    knowledge = config["private_knowledge"]
    # The caller materializes this metadata through the authenticated connector.
    observed = json.loads((args.cache / "repository.json").read_text())
    if str(observed["id"]) != knowledge["repository_id"]:
        raise ValueError("KB_ACCESS_DENIED: unexpected repository ID")
    snapshot = Snapshot.from_reader(
        args.commit, lambda ref, path: (args.cache / ref / path).read_bytes(),
        knowledge["registry_path"], repository_id=observed["id"],
        repository=observed["repository_full_name"], visibility=observed["visibility"],
    )
    if args.stage == "search":
        result = snapshot.search(args.query, args.platform, args.domain, args.kind, args.status,
                                 adapter_id=args.adapter_id, industry_tag=args.industry_tag,
                                 business_model=args.business_model, buyer_role=args.buyer_role,
                                 content_goal=args.content_goal)
    elif args.stage == "read":
        if not args.id:
            parser.error("read needs --id")
        result = snapshot.read(args.id, args.offset, include_history=args.include_history)
    else:
        result = snapshot.status()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
