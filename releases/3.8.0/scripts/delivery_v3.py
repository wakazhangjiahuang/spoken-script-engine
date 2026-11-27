"""Workbook publication after readback from the candidate export."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from execution_contract import digest, read
from production_v3 import write_cards


def export_with_readback(run_export, argv, output, run, batch, production=None, mode="none"):
    from openpyxl import load_workbook

    if output is None or output.suffix.lower() != ".xlsx":
        raise ValueError("M11 requires a workbook output path ending in .xlsx")
    manifest = output.with_suffix(".delivery.json")
    if output.exists() or manifest.exists():
        raise ValueError("M11 output already exists; use a new versioned filename")
    args = [part for part in argv]
    flag_index = next((i for i, arg in enumerate(args) if arg == "--output" or arg.startswith("--output=")), None)
    if flag_index is None:
        raise ValueError("M11 requires --output")
    with TemporaryDirectory(dir=output.parent) as scratch:
        workbook = Path(scratch) / output.name
        if args[flag_index] == "--output":
            args[flag_index + 1] = str(workbook)
        else:
            args[flag_index] = f"--output={workbook}"
        run_export(args)
        if mode != "none":
            production_book = load_workbook(workbook)
            try:
                write_cards(production_book, production, mode)
                production_book.save(workbook)
            finally:
                production_book.close()
        loaded = load_workbook(workbook)
        try:
            sheet_names = loaded.sheetnames
            script_ids = {s["id"] for s in batch["scripts"]}
            hits = {s: [] for s in script_ids}
            for sheet in loaded:
                for row in sheet.iter_rows(values_only=True):
                    if len(row) == 17 and row[0] in script_ids:
                        hits[row[0]].append((sheet.title, row))
            field_map = {}
            for kind, name in (("04", "04真人分段指令"), ("05", "05 H3逐镜指令")):
                if kind in mode:
                    actual = [row[:4] for row in loaded[name].iter_rows(min_row=2, values_only=True)]
                    expected = [(card["script_id"], shot["id"], shot["segment_id"], shot["text"])
                                for card in production["cards"] for shot in card[kind]]
                    if actual != expected:
                        raise ValueError(f"M11 {kind} card transcript readback failed")
            for script in batch["scripts"]:
                script_id = script["id"]
                if len(hits[script_id]) != 1:
                    raise ValueError(f"M11 readback could not resolve one script row: {script_id}")
                sheet_name, row = hits[script_id][0]
                speech = "\n".join(seg["text"] for seg in script["segments"])
                comment = script["comment_hook"]["line"]
                if (row[2], row[3], row[4], row[16]) != (
                        script["audience"], script["cover_main"], script["cover_sub"], speech
                ) or row[9] not in {comment, "不并行启用：" + comment}:
                    raise ValueError(f"M11 readback of lock, speech or comments failed: {script_id}")
                field_map[script_id] = sheet_name
        finally:
            loaded.close()
        status = read(run / "v3.6.1-validation-status.json")["status"]
        record = {"version": "3.8.0", "file_name": output.name, "sha256": digest(workbook),
                  "sheet_names": sheet_names, "script_to_sheet": field_map, "lock_check": "PASS",
                  "readback_status": "PASS", "acceptance_status": status}
        candidate = Path(scratch) / manifest.name
        candidate.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.link(workbook, output)
        try:
            os.link(candidate, manifest)
        except OSError:
            output.unlink()
            raise
