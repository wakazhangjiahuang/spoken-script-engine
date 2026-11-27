"""M13 records genuine publication evidence and keeps promotion review separate."""
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from decision_v3 import require, text_fields
from execution_contract import digest


def validate_outcome(record, run):
    text_fields(record, ("script_id", "status"), "M13")
    if record["status"] == "NOT_RUN":
        require(not any(key in record for key in ("metrics", "published_at", "url")),
                "OUTCOME_NOT_OBSERVED", "M13", "unpublished results carry no invented zero or link")
        return
    require(record["status"] == "OBSERVED", "OUTCOME_STATUS_INVALID", "M13", record["status"])
    text_fields(record, ("url", "published_at", "window_start", "window_end", "baseline",
                         "attribution_limit", "evidence_file", "evidence_sha256", "platform", "account"),
                "M13")
    address = urlparse(record["url"])
    require(address.scheme == "https" and bool(address.netloc), "PUBLICATION_LINK_INVALID", "M13", "URL")
    clocks = [datetime.fromisoformat(record[key]) for key in ("published_at", "window_start", "window_end")]
    require(all(t.tzinfo for t in clocks) and clocks[0] <= clocks[1] < clocks[2],
            "OUTCOME_WINDOW_INVALID", "M13", "use the observed timezone and window")
    run = run.resolve()
    evidence = (run / record["evidence_file"]).resolve()
    require(evidence.is_relative_to(run) and evidence.is_file() and digest(evidence) == record["evidence_sha256"],
            "OUTCOME_EVIDENCE_MISMATCH", "M13", "keep original platform/CRM evidence")
    metrics = record.get("metrics")
    require(isinstance(metrics, list) and bool(metrics), "OUTCOME_METRICS_MISSING", "M13", "no observed metric")
    for metric in metrics:
        text_fields(metric, ("name", "event", "denominator_event"), "M13")
        numerator, denominator = metric.get("numerator"), metric.get("denominator")
        require(type(numerator) is int and type(denominator) is int and 0 <= numerator <= denominator
                and denominator > 0, "OUTCOME_DENOMINATOR_INVALID", "M13", metric["name"])
    promotion = record.get("promotion", "retain_observation")
    require(promotion in {"retain_observation", "request_review"},
            "PROMOTION_REQUIRES_APPROVAL", "M13", "promotion is a separate editorial decision")


def record_outcome(run: Path, input_path: Path):
    from execution_contract import canonical, read
    from proposal_handoff import write_same, selected_topics

    handoff = read(run / "a-handoff.json")
    selected = set(selected_topics(handoff))
    record = read(input_path)
    accepted = read(run / "v3.6.1-validation-status.json")
    require(accepted["stage"] in {"validate", "export"} and
            accepted["status"] in {"PASS", "VALIDATION_PENDING"},
            "OUTCOME_RUN_UNACCEPTED", "M13", "complete the editorial stage")
    batches = sorted(run.glob("batch-v*.json"))
    require(bool(batches), "OUTCOME_SCRIPT_MISSING", "M13", "no canonical batch")
    scripts = {s["id"]: s for s in read(batches[-1])["scripts"] if s["plan_id"] in selected}
    require(record.get("script_id") in scripts, "OUTCOME_SCRIPT_MISSING", "M13", str(record.get("script_id")))
    validate_outcome(record, run)
    write_same(run / ("outcome-" + canonical(record)[:16] + ".json"), record)
