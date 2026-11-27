"""M10 execution-card validation against canonical scripts and original material IDs."""
from decision_v3 import ids, require, text_fields

MODES = {"none", "04", "05", "04+05"}
STAGES = ("content", "facts", "storyboard", "materials", "h3", "final")
ASSET_ROLES = {"P01", "P02", "P03", "A01", "R"}
BASE = ("id", "segment_id", "text", "subject", "shot_size", "camera", "action",
        "cut_point", "subtitle", "sound", "acceptance")


def validate_production(record, mode, batch):
    require(mode in MODES, "PRODUCTION_MODE_INVALID", "M10", str(mode))
    if mode == "none":
        return
    text_fields(record, ("plan_id",), "M10")
    gates = ids(record.get("gates"), "id", "M10")
    require(set(gates) == set(STAGES), "PRODUCTION_GATE_COVERAGE", "M10", mode)
    for stage, gate in gates.items():
        text_fields(gate, ("status", "reason"), "M10")
        require(gate["status"] in {"PASS", "NOT_RUN", "NOT_APPLICABLE"},
                "PRODUCTION_GATE_BLOCKED", "M10", stage)
        if stage in {"content", "facts", "storyboard", "materials"} or gate["status"] == "PASS":
            require(gate["status"] == "PASS" and bool(gate.get("evidence_refs")),
                    "PRODUCTION_GATE_UNSUPPORTED", "M10", stage)
    assets = ids(record.get("assets"), "id", "M10") if record.get("assets") else {}
    for key, asset in assets.items():
        text_fields(asset, ("role", "source_id", "locator", "rights"), "M10")
        require(asset["role"] in ASSET_ROLES and asset["rights"] in {"authorized", "public"},
                "PRODUCTION_ASSET_RIGHTS_HOLD", "M10", key)
    scripts = ids(batch["scripts"], "id", "M10")
    cards = ids(record.get("cards"), "script_id", "M10")
    require(set(cards) == set(scripts), "PRODUCTION_SCRIPT_COVERAGE", "M10", mode)
    for script_id, card in cards.items():
        script = scripts[script_id]
        segments = ids(script["segments"], "id", "M10")
        for which in ("04", "05"):
            if which in mode:
                validate_segments(which, card.get(which), segments, assets, script_id)
            else:
                require(not card.get(which), "PRODUCTION_MODE_MISMATCH", "M10", script_id)


def validate_segments(kind, rows, segments, assets, script_id):
    shots = ids(rows, "id", "M10")
    coverage = {}
    for shot_id, row in shots.items():
        text_fields(row, BASE, "M10")
        segment = row["segment_id"]
        require(segment in segments, "SHOT_SEGMENT_LOOKUP", "M10", shot_id)
        coverage.setdefault(segment, []).append(row)
        refs = row.get("asset_ids", [])
        require(isinstance(refs, list) and all(key in assets for key in refs),
                "SHOT_ASSET_LOOKUP", "M10", shot_id)
        require(row.get("duration_seconds", 0) > 0, "SHOT_TIMING_REQUIRED", "M10", shot_id)
        if kind == "05":
            text_fields(row, ("prompt", "negative_constraints", "lighting", "motion",
                              "expression", "background", "selection"), "M10")
            generated = row.get("generation_asset_ids", [])
            post = row.get("post_insert_asset_ids", [])
            require(set(generated) | set(post) == set(refs) and not set(generated) & set(post),
                    "H3_ASSET_ROLE_MAPPING", "M10", shot_id)
            require(all(assets[key]["role"] != "R" for key in generated) and
                    all(assets[key]["role"] == "R" for key in post),
                    "H3_REAL_EVIDENCE_POST_ONLY", "M10", shot_id)
    require(list(coverage) == list(segments), "SHOT_SEGMENT_ORDER_OR_COVERAGE", "M10", script_id)
    for seg, row in segments.items():
        mapped = coverage[seg]
        require("".join(shot["text"] for shot in mapped) == row["text"],
                "SHOT_LINE_DRIFT", "M10", f"{script_id}/{seg}")
        require(abs(sum(shot["duration_seconds"] for shot in mapped) - row["duration_seconds"]) < 0.05,
                "SHOT_TIME_DRIFT", "M10", f"{script_id}/{seg}")


def write_cards(workbook, production, mode):
    if mode == "none":
        return
    for kind, name in (("04", "04真人分段指令"), ("05", "05 H3逐镜指令")):
        if kind not in mode:
            continue
        sheet = workbook.create_sheet(name)
        extra = ("prompt", "negative_constraints", "lighting", "motion", "expression",
                 "background", "selection", "post_insert_asset_ids") if kind == "05" else ()
        columns = ("script_id", *BASE, "duration_seconds", "asset_ids", *extra)
        headers = {"script_id": "脚本ID", "id": "镜头ID", "segment_id": "段落ID", "text": "逐字台词",
                   "subject": "人物或物件", "shot_size": "景别", "camera": "机位", "action": "动作",
                   "cut_point": "切点", "subtitle": "字幕", "sound": "声音", "acceptance": "验收点",
                   "duration_seconds": "估计秒数", "asset_ids": "素材ID", "prompt": "逐镜提示词",
                   "negative_constraints": "负面约束", "lighting": "灯光", "motion": "运镜",
                   "expression": "情绪", "background": "背景", "selection": "选材指令",
                   "post_insert_asset_ids": "后插真实素材ID"}
        sheet.append([headers[c] for c in columns])
        for card in production["cards"]:
            for shot in card[kind]:
                row = {"asset_ids": [], "post_insert_asset_ids": [], **shot, "script_id": card["script_id"]}
                sheet.append(["、".join(row[c]) if isinstance(row[c], list) else row[c] for c in columns])
                # Text originating in external records must remain literal spreadsheet text.
                for cell in sheet[sheet.max_row]:
                    if isinstance(cell.value, str):
                        cell.data_type = "s"
        sheet.freeze_panes = "E2"
        sheet.auto_filter.ref = sheet.dimensions
        for column in sheet.columns:
            sheet.column_dimensions[column[0].column_letter].width = 20
        sheet.column_dimensions["D"].width = 50
