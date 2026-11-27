"""A-only proposal export and exact A-to-B bindings for the existing runner."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

from execution_contract import canonical, digest, fresh, read
import decision_v3 as v3

COPY = ("cover_main", "cover_sub", "hook", "suspense", "body", "calling", "comment")
LOCKABLE = set(COPY) - {"body"}
PLAN = ("platform", "buyer_decision", "payoff", "next_step")
BRIEF_CONTEXT = (
    "topic", "audience", "goal", "domain", "quality_profile", "objective", "content_task",
    "content_context", "case_policy", "facts", "source_inventory",
    "product_advantage_evidence",
)
TITLES = ("主标题", "副标题", "黄金开场", "3–8 秒", "正文示范", "Calling", "评论")
TOPIC_ID = re.compile(r"[\w-]{1,64}")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonblank(value):
    return isinstance(value, str) and bool(value.strip())


def indexed(rows, field):
    require(isinstance(rows, list) and bool(rows), f"{field} list is empty")
    result = {}
    for row in rows:
        key = row.get(field) if isinstance(row, dict) else None
        require(nonblank(key) and TOPIC_ID.fullmatch(key) and key not in result,
                f"invalid or repeated {field}: {key}")
        result[key] = row
    return result


def validate_locks(copy, locks, topic):
    require(isinstance(locks, dict) and set(locks) <= LOCKABLE, f"{topic}: unknown locked field")
    for field, lock in locks.items():
        require(isinstance(lock, dict) and nonblank(lock.get("text")) and
                lock.get("scope") in {"exact", "prefix"}, f"{topic}: invalid lock for {field}")
        value = copy.get(field)
        require(isinstance(value, str) and
                (value == lock["text"] if lock["scope"] == "exact" else value.startswith(lock["text"])),
                f"{topic}: changed {lock['scope']} lock on {field}")


def source_hashes(run):
    manifest = read(run / "source-manifest.json")
    receipt = read(run / "event-001.json")["files"]
    require(receipt.get("source-manifest.json") == digest(run / "source-manifest.json") and
            receipt.get("brief.json") == digest(run / "brief.json"),
            "original intake receipt and sources do not match")
    sources = manifest["sources"]
    require(bool(sources), "original request is missing")
    hashes = []
    for source in sources:
        relative = source["stored_path"]
        path = (run / relative).resolve()
        require(path.is_relative_to(run.resolve()) and receipt.get(relative) == source["sha256"] == digest(path),
                "an intake source changed")
        hashes.append(source["sha256"])
    return hashes


def source_ids(brief):
    inventory = brief.get("source_inventory", {})
    return (
        {row["id"] for row in brief.get("facts", []) + brief.get("production_resources", [])}
        | {row["asset_id"] for row in inventory.get("checked_assets", [])}
    )


def locks_for(brief, topic_id):
    return {
        key: value
        for row in brief.get("copy_locks", [])
        if row["plan_id"] == topic_id
        for key, value in row.items()
        if key in LOCKABLE
    }


def intake_locks(run):
    path = run / "a-locks.json"
    expected = read(run / "event-001.json")["files"].get(path.name)
    if path.exists() or expected is not None:
        require(path.is_file() and digest(path) == expected, "A's declared locks changed")
        return read(path)
    return {}


def brief_context(brief):
    return {key: brief[key] for key in BRIEF_CONTEXT if key in brief}


def validate_proposal(topics, brief, required_locks, context=None):
    allowed_sources = source_ids(brief)
    require(required_locks.keys() <= topics.keys(), "a topic from the intake locks is missing")
    seen = set()
    for topic_id, row in topics.items():
        require(all(nonblank(row.get(key)) for key in (*PLAN, "audience")),
                f"{topic_id}: missing task, audience, payoff or action")
        copy = row.get("copy")
        require(isinstance(copy, dict) and set(copy) == set(COPY) and all(map(nonblank, copy.values())),
                f"{topic_id}: proposal requires actual copy in all seven fields")
        locks = row.get("locks", {})
        validate_locks(copy, locks, topic_id)
        for field, text in locks_for(brief, topic_id).items():
            require(locks.get(field) == {"scope": "exact", "text": text},
                    f"{topic_id}: intake requires an exact {field} lock")
        for field, lock in required_locks.get(topic_id, {}).items():
            require(locks.get(field) == lock, f"{topic_id}: A changed or omitted the declared {field} lock")
        refs = row.get("evidence_refs")
        require(isinstance(refs, list) and bool(refs) and all(
            isinstance(ref, str) and ref in allowed_sources for ref in refs),
            f"{topic_id}: missing or unknown source reference")
        signature = (row["platform"], " ".join(row["buyer_decision"].split()).casefold())
        require(signature not in seen, f"{topic_id}: repeated customer decision on this platform")
        seen.add(signature)

    if context is not None:
        per_platform = set()
        for row in topics.values():
            decision = v3.validate_topic(row, brief)
            require(len(row["copy"]["body"]) <= 200, "A can give a brief proof example only")
            key = (row["platform"], v3.normalized(decision["unique_payoff"]))
            require(key not in per_platform, f"{row['id']}: repeated customer payoff on this platform")
            per_platform.add(key)

    expected = Counter({platform: brief.get("count_per_platform", {}).get(platform, 3)
                        for platform in brief["platforms"]})
    require(Counter(row["platform"] for row in topics.values()) == expected,
            "proposal does not match the platform and counts from intake")


def proposal(run, input_path, output_path):
    require(not (run / "decision.json").exists() and not (run / "a-handoff.json").exists(),
            "use the original A intake for the proposal")
    hashes = source_hashes(run)
    brief = read(run / "brief.json")
    data = read(input_path)
    topics = indexed(data["topics"], "id")
    context = run_context(run)
    validate_proposal(topics, brief, intake_locks(run), context)
    record = {"version": 2 if context else 1, "source_hashes": hashes, "brief_context": brief_context(brief),
              "topics": list(topics.values())}
    if context:
        record["run_context"] = context
    target = run / "a-proposal.json"
    write_same(target, record)
    lines = []
    for topic in topics.values():
        lines += [f"## {topic['id']} · {topic['platform']}", ""]
        if context:
            d = topic["decision_v3"]
            customer, purchase = d["customer"], d["purchase"]
            winner = next(item for item in d["entries"] if item["id"] == d["value_map"]["entry_id"])
            lines.extend([
                f"- 受众与任务｜{topic['audience']} · {customer['buyer_role']} · {customer['context']} · {customer['current_task']}",
                f"- 根本需求与回报｜{customer['root_need']} · {topic['payoff']}",
                f"- 品类选择｜{d['category']['reason']}",
                f"- 项目理由｜{purchase['status']} · {purchase['reason']} · {purchase['claim_limit']}",
                f"- 胜出入口｜{winner['question']} · {winner['rationale']}",
                f"- 证据与风险｜{', '.join(topic['evidence_refs'])} · {d['risk']}",
                f"- 平台任务｜{d['value_map']['platform_task']} · {d['platform_difference']}",
                "",
            ])
        for field, title in zip(COPY, TITLES):
            lines += [f"**{title}**", "", topic["copy"][field], ""]
    rendered = "\n".join(lines)
    if output_path:
        require(output_path.resolve() not in {input_path.resolve(), target.resolve()},
                "proposal output must be a separate text file")
        with output_path.open("x", encoding="utf-8") as stream:
            stream.write(rendered)
    else:
        print(rendered)


def write_same(path, value):
    if path.exists():
        require(read(path) == value, f"{path.name} has already been sealed; start a new run for changes")
    else:
        fresh(path, value)


def select(run, ids, authorization, output):
    target = run / "a-proposal.json"
    record = read(target)
    require(source_hashes(run) == record["source_hashes"], "A sources changed")
    topics = indexed(record["topics"], "id")
    brief = read(run / "brief.json")
    require(brief_context(brief) == record["brief_context"], "A brief changed")
    context = run_context(run)
    require(record.get("run_context") == context, "A knowledge and route snapshot changed")
    validate_proposal(topics, brief, intake_locks(run), context)
    require(len(set(ids)) == len(ids) and set(ids) <= topics.keys(), "select only known and unique topic IDs")
    require(nonblank(authorization), "record the user's confirmation or direct-draft request")
    if context and context["execution_mode"] == "direct":
        source = read(run / "source-manifest.json")["sources"][0]["stored_path"]
        require(authorization.strip() in (run / source).read_text(encoding="utf-8"),
                "direct-draft authorization must be quoted from this run's original request")
    handoff = {
        "version": record["version"],
        "proposal": record,
        "proposal_sha256": canonical(record),
        "topic_ids": ids,
        "authorization": authorization,
    }
    fresh(output, handoff)


def selected_topics(handoff):
    record = handoff["proposal"]
    require(handoff.get("version") == record.get("version") in {1, 2} and
            handoff["proposal_sha256"] == canonical(record),
            "A proposal changed after selection")
    topics = indexed(record["topics"], "id")
    ids = handoff["topic_ids"]
    require(isinstance(ids, list) and ids and len(set(ids)) == len(ids) and
            set(ids) <= topics.keys() and nonblank(handoff.get("authorization")),
            "invalid handoff selection or missing authorization")
    if handoff["version"] == 2:
        v3.validate_context(record["run_context"])
    return {key: topics[key] for key in ids}


def check_b_brief(handoff, brief, source_digests):
    topics = selected_topics(handoff)
    require(source_digests == handoff["proposal"]["source_hashes"], "B must use the same original request and sources")
    require(brief_context(brief) == handoff["proposal"]["brief_context"],
            "B changed the approved A task context or facts")
    counts = Counter(row["platform"] for row in topics.values())
    require(set(brief["platforms"]) == counts.keys() and
            counts == {p: brief.get("count_per_platform", {}).get(p, 3) for p in brief["platforms"]},
            "B's platform counts must match the selected topics")
    for topic_id, row in topics.items():
        if handoff["version"] == 2:
            v3.validate_topic(row, brief)
        require(all(ref in source_ids(brief) for ref in row["evidence_refs"]),
                f"{topic_id}: B lost a required source reference")


def check_b_plan(handoff, plan):
    topics = selected_topics(handoff)
    rows = indexed(plan["selected"], "id")
    require(rows.keys() == topics.keys(), "B must plan only the selected topic IDs")
    for topic_id, row in rows.items():
        if handoff["version"] == 2:
            require(row.get("v3_handoff_sha256") == canonical(topics[topic_id]["decision_v3"]),
                    f"HANDOFF_DRIFT [M07] {topic_id}: purchase reason, entry and promise")
        for field in PLAN:
            require(row.get(field) == topics[topic_id][field], f"{topic_id}: B changed {field}")


def check_b_batch(handoff, batch):
    topics = selected_topics(handoff)
    scripts = indexed(batch["scripts"], "plan_id")
    require(scripts.keys() == topics.keys(), "B must draft only the selected topic IDs")
    for topic_id, script in scripts.items():
        topic = topics[topic_id]
        require(script.get("platform") == topic["platform"] and script.get("audience") == topic["audience"],
                f"{topic_id}: B changed platform or audience")
        segments = {segment["role"]: segment["text"] for segment in script["segments"]}
        actual = {key: script.get(key) for key in ("cover_main", "cover_sub")}
        actual.update({key: segments.get(key) for key in ("hook", "suspense", "calling")})
        actual["comment"] = script.get("comment_hook", {}).get("line")
        validate_locks(actual, topic.get("locks", {}), topic_id)
    if handoff["version"] == 2:
        v3.validate_draft(batch, topics)


def run_context(run):
    receipt = read(run / "event-001.json")
    path = run / "v3-run-context.json"
    expected = receipt["files"].get(path.name)
    if not expected:
        require(not path.exists(), "unsealed V3 run context")
        return None
    require(path.is_file() and digest(path) == expected, "V3 run context changed")
    context = read(path)
    v3.validate_context(context)
    return context


def route(argv, legacy_main):
    if argv and argv[0] == "record-outcome":
        from outcome_v3 import record_outcome
        parser = argparse.ArgumentParser()
        parser.add_argument("stage", choices=["record-outcome"])
        parser.add_argument("--run", type=Path, required=True)
        parser.add_argument("--input", type=Path, required=True)
        args = parser.parse_args(argv)
        return record_outcome(args.run, args.input)
    if argv and argv[0] in {"proposal", "select"}:
        parser = argparse.ArgumentParser()
        parser.add_argument("stage", choices=["proposal", "select"])
        parser.add_argument("--run", type=Path, required=True)
        if argv[0] == "proposal":
            parser.add_argument("--input", type=Path, required=True)
            parser.add_argument("--output", type=Path)
            args = parser.parse_args(argv)
            return proposal(args.run, args.input, args.output)
        parser.add_argument("--topic", action="append", required=True)
        parser.add_argument("--authorization", required=True)
        parser.add_argument("--output", type=Path, required=True)
        args = parser.parse_args(argv)
        return select(args.run, args.topic, args.authorization, args.output)

    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--handoff", type=Path)
    parser.add_argument("--mode", choices=["A", "B"])
    parser.add_argument("--locks", type=Path)
    parser.add_argument("--run-context", type=Path)
    args, legacy_argv = parser.parse_known_args(argv)
    is_intake = legacy_argv[:1] == ["intake"]
    if is_intake and args.mode is None:
        args.mode = "B" if args.handoff else "A"
    require(args.run_context is None or (is_intake and args.mode == "A"),
            "--run-context is accepted only by A intake")
    require(args.locks is None or args.mode == "A", "--locks is accepted only by A intake")
    if args.mode:
        require(legacy_argv[:1] == ["intake"], "--mode is accepted only by intake")
        require((args.mode == "B") == (args.handoff is not None), "B intake requires a handoff; A intake starts from sources")
    if legacy_argv[:1] == ["intake"] and (args.handoff or args.mode == "A"):
        flags = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
        flags.add_argument("--run", type=Path, required=True)
        flags.add_argument("--input", type=Path, required=True)
        flags.add_argument("--request", type=Path, required=True)
        flags.add_argument("--source", type=Path, action="append", default=[])
        intake, _ = flags.parse_known_args(legacy_argv)
        handoff = read(args.handoff) if args.handoff else None
        require(handoff is not None or args.run_context is not None,
                "new intake needs --run-context for V3 route and pinned knowledge")
        context = handoff["proposal"].get("run_context") if handoff else read(args.run_context)
        if context is not None:
            v3.validate_context(context)
        locks = read(args.locks) if args.locks else None
        if locks is not None:
            require(isinstance(locks, dict), "A locks must map topic IDs to locked fields")
            for topic_id, fields in locks.items():
                require(TOPIC_ID.fullmatch(topic_id) and isinstance(fields, dict), "invalid A locks record")
                # Validate field names and modes before the intake writes any state.
                require(all(isinstance(lock, dict) for lock in fields.values()), "invalid A lock value")
                validate_locks({key: lock.get("text") for key, lock in fields.items()}, fields, topic_id)
        if handoff:
            sources = [intake.request, *intake.source]
            check_b_brief(handoff, read(intake.input), [digest(path) for path in sources])
        legacy_main(legacy_argv)
        receipt_path = intake.run / "event-001.json"
        receipt = read(receipt_path)
        receipt["task_mode"] = "B" if handoff else "A"
        if context is not None:
            target = intake.run / "v3-run-context.json"
            fresh(target, context)
            receipt["files"][target.name] = digest(target)
        if handoff:
            check_b_brief(handoff, read(intake.run / "brief.json"), source_hashes(intake.run))
            target = intake.run / "a-handoff.json"
            fresh(target, handoff)
            receipt["files"][target.name] = digest(target)
        if locks is not None:
            target = intake.run / "a-locks.json"
            fresh(target, locks)
            receipt["files"][target.name] = digest(target)
        updated = intake.run / "event-intake.tmp"
        fresh(updated, receipt)
        updated.replace(receipt_path)
        return

    require(args.handoff is None, "--handoff is accepted only by intake")
    if legacy_argv and legacy_argv[0] in {"plan", "draft", "validate", "export"}:
        flags = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
        flags.add_argument("--run", type=Path, required=True)
        flags.add_argument("--input", type=Path)
        flags.add_argument("--review", type=Path)
        flags.add_argument("--output", type=Path)
        parsed, _ = flags.parse_known_args(legacy_argv)
        run = parsed.run
        require(not (run / "a-proposal.json").exists(), "A ends at proposal; start B intake with the selected handoff")
        path = run / "a-handoff.json"
        event = run / "event-001.json"
        receipt = read(event) if event.exists() else {}
        require(receipt.get("task_mode") != "A", "finish A first and open a separate B run with the handoff")
        files = receipt.get("files", {})
        if receipt.get("task_mode") == "B" or path.exists() or path.name in files:
            require(path.is_file() and digest(path) == files.get(path.name), "sealed B handoff is missing or changed")
            handoff = read(path)
            check_b_brief(handoff, read(run / "brief.json"), source_hashes(run))
            require(parsed.input is not None, "B requires an input file")
            if handoff["version"] == 2:
                require(run_context(run) == handoff["proposal"]["run_context"],
                        "HANDOFF_DRIFT [M03] B changed its knowledge snapshot")
            if legacy_argv[0] == "plan":
                check_b_plan(handoff, read(parsed.input))
            else:
                check_b_plan(handoff, read(run / "decision.json"))
                batch = read(parsed.input)
                check_b_batch(handoff, batch)
                if handoff["version"] == 2:
                    if legacy_argv[0] in {"validate", "export"}:
                        require(parsed.review is not None, "V3 requires the independent review")
                        review = read(parsed.review)
                        reviewer = review.get("reviewer_attestation", {})
                        v3.validate_review(batch, selected_topics(handoff), review.get("v3_acceptance"),
                                           digest(parsed.input), reviewer.get("reviewer_id"))
                        from production_v3 import validate_production
                        mode = handoff["proposal"]["run_context"].get("production_mode", "none")
                        production = review.get("v3_production")
                        validate_production(production, mode, batch)
                        if legacy_argv[0] == "export":
                            from delivery_v3 import export_with_readback
                            return export_with_readback(legacy_main, legacy_argv, parsed.output, run, batch,
                                                        production, mode)
    return legacy_main(legacy_argv)
