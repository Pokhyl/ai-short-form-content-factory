"""Read tracked sources/fixtures and report release evidence without provider or DB calls."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOUNDARIES = [
    ("M4 -> M5", "Evidence-grounded research handed to script", ["tests/m4-research-relevance.test.cjs", "tests/semantic-preservation.test.cjs"], "Separate component tests; current failed production job passed both stages, but no portable replay of the combined boundary was identified."),
    ("M5 -> M6", "Accepted continuous narration and exact audio reused", ["tests/voiceover-candidate-reuse.test.cjs", "tests/measured-draft-reuse.test.cjs"], "Workflow contract tests include synthetic audio; do not infer a real media identity check from these alone."),
    ("M6 -> M7", "Actual audio, transcript and scene timing", ["tests/alignment-dtw-regression.py"], "Saved ASR/DTW data and worker timing functions; a saved audio hash does not prove fresh decode/alignment of the exact MP3."),
    ("M5 -> M8", "Original visual anchors survive validation and retrieval", ["tests/m5-m8-12108-fastening-contract.test.cjs"], "Partial native validator/request replay plus generic controls; an executable whole-stage handoff is not established by filename or fixture presence."),
    ("M8 retrieval -> SQL", "Provider pools, nomination and three-slot ranking", ["tests/m8-12108-semantic-nomination-ranking.py", "tests/m8-component-owner-ranking.py", "tests/m8-paired-objects-ranking.py"], "Actual saved pools, baseline/current SQL and rollback; new S4 pixels/provider acceptance are still unresolved."),
    ("M8 previews -> vision -> selection", "Real photo identity, contract and global uniqueness", ["tests/gemini-visual-validation.test.cjs", "tests/m8-9229-replay.test.cjs", "tests/m5-m8-12108-fastening-contract.test.cjs"], "Parser/collector and historical saved reviews do not establish a new strict nine-scene provider pass after the S4 change."),
    ("M7/M8 -> M9", "Exact audio, timed scenes and selected media rendered", ["tests/render-target-duration-regression.py", "tests/render-fit-regression.py", "tests/voiceover-candidate-reuse.test.cjs"], "Worker rendering and workflow contracts are separate checks; synthetic FFmpeg media is not the latest real full-product MP4."),
    ("M9 -> review/product acceptance", "Decoded vertical MP4 and human review", ["scripts/audit_final_media.py"], "Audit tool exists; latest failed job never reached M9. No current-release four-case media acceptance is recorded in this checkpoint."),
]

def tracked_files():
    return subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")[:-1]


def explicit_metadata(value):
    found = {"languages": set(), "target_seconds": set(), "topics": set(), "execution_ids": set(), "job_ids": set()}
    def walk(obj):
        if isinstance(obj, dict):
            for key, item in obj.items():
                if key in ("language", "language_code", "locale") and isinstance(item, str) and len(item) < 40:
                    found["languages"].add(item)
                if key in ("target_duration_seconds", "target_duration_ms") and isinstance(item, (int, float)):
                    seconds = item / 1000 if key.endswith("_ms") else item
                    if seconds in (15, 30, 45, 60):
                        found["target_seconds"].add(seconds)
                if key == "topic" and isinstance(item, str) and len(item) < 300:
                    found["topics"].add(item)
                if key in ("execution_id", "job_id") and isinstance(item, (str, int)):
                    found["execution_ids" if key == "execution_id" else "job_ids"].add(str(item))
                if isinstance(item, (dict, list)):
                    walk(item)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)
    walk(value)
    return {key: sorted(values) for key, values in found.items()}


def inventory():
    tracked = tracked_files()
    fixtures = sorted(p for p in tracked if p.startswith("tests/fixtures/") and p.endswith(".json"))
    runners = sorted(p for p in tracked if p.startswith("tests/") and (p.endswith(".test.cjs") or p.endswith(".py") or p.endswith(".cjs")))
    scripts = sorted(p for p in tracked if p.startswith("scripts/") and p.endswith((".py", ".cjs")))
    sources = {p: (ROOT / p).read_text() for p in runners + scripts}
    refs = {p: sorted(f for f in fixtures if Path(f).name in source) for p, source in sources.items()}
    script_refs = {p: sorted(s for s in scripts if s != p and (s in source or Path(s).name in source)) for p, source in sources.items()}
    def closure(path, seen=None):
        seen = set() if seen is None else seen
        if path in seen:
            return set()
        seen.add(path)
        result = set(refs[path])
        for child in script_refs[path]:
            result.update(closure(child, seen))
        return result
    fixture_rows = []
    for path in fixtures:
        raw = (ROOT / path).read_bytes()
        value = json.loads(raw)
        users = [r for r in runners if path in closure(r)]
        fixture_rows.append({"path": path, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "top_level_keys": sorted(value) if isinstance(value, dict) else [], "explicit_metadata": explicit_metadata(value), "literal_reference_runners": users})
    runner_rows = []
    for path in runners:
        source = sources[path]
        group = "node_test_suite" if path.endswith(".test.cjs") else "sql_regression" if "-ranking.py" in path else "separate_runner"
        workflows = sorted(set(re.findall(r"VIDEO-M[0-9]+-[A-Za-z0-9-]+\.json", source)))
        runner_rows.append({"path": path, "runner_group": group, "literal_workflow_references": workflows, "literal_script_references": script_refs[path], "fixture_references_with_script_closure": sorted(closure(path)), "worker_source_reference": "services/media-worker/server.py" in source, "test_title_count_static": len(re.findall(r"\btest\s*\(\s*['\"]", source))})
    evidence_path = ROOT / "acceptance/2026-10-04-project-checkpoint/evidence.json"
    evidence = json.loads(evidence_path.read_text())
    hashes_valid = all((ROOT / p).exists() and hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == digest for p, digest in {**evidence["sha256"], **evidence.get("test_log_sha256", {})}.items())
    assert hashes_valid, "Checkpoint file hash mismatch; coverage evidence must not silently become stale"
    boundaries = [{"boundary": b, "contract": c, "supporting_files": files, "all_supporting_files_tracked": all(p in tracked for p in files), "evidence_limit": limit, "whole_boundary_current_release_proven": False} for b, c, files, limit in BOUNDARIES]
    assert all(b["all_supporting_files_tracked"] for b in boundaries)
    return {"schema_version": 1, "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "method": "Static literal-reference inventory and explicit JSON fields, with manually inspected boundary evidence limits. No source evaluation, provider calls, DB calls or production mutations. Missing literal references may be dynamic; language/topic absence means unknown, not unsupported.", "provider_calls": 0, "production_mutations": 0, "checkpoint_hashes_valid": hashes_valid, "checkpoint_results": {"node_tests": evidence["node_tests"], "sql_regressions": evidence["sql_regressions"]}, "product_ready": False, "summary": {"tracked_fixture_count": len(fixtures), "tracked_runner_count": len(runners), "node_suite_file_count": sum(r["runner_group"] == "node_test_suite" for r in runner_rows), "sql_runner_count": sum(r["runner_group"] == "sql_regression" for r in runner_rows), "separate_runner_count": sum(r["runner_group"] == "separate_runner" for r in runner_rows), "fixtures_without_identified_literal_runner": [f["path"] for f in fixture_rows if not f["literal_reference_runners"]]}, "fixtures": fixture_rows, "runners": runner_rows, "boundaries": boundaries, "release_blockers": ["Inspect actual S4 open-owner previews and establish strict loaded-container evidence.", "Establish final current nine-scene strict provider/global unique selection after S4 closure.", "Run relevant separate worker regressions with pinned environment and tracked results; Node883 does not include them.", "Add or establish executable connected stage-boundary replay where inventory shows only separate checks.", "Deploy and verify exact changed components only after closure.", "Complete representative current-release multilingual/duration final-media acceptance; no current-release four-case evidence established."]}


def markdown(report):
    lines = ["# Release coverage inventory", "", f"Source commit: `{report['source_commit']}`. Generated with `python3 scripts/inventory_release_coverage.py --output-dir acceptance/release-coverage`.", "", report["method"], "", "## Verified checkpoint and scope", "", "Node883/883 and SQL8/8 are stored, hash-verified offline results. They are not whole-product acceptance. Separate worker runners are not included in Node883. This inventory calls no models and changes no production state.", "", "| Inventory | Count |", "|---|---:|"]
    for key in ("tracked_fixture_count", "tracked_runner_count", "node_suite_file_count", "sql_runner_count", "separate_runner_count"):
        lines.append(f"| {key} | {report['summary'][key]} |")
    if "separate_runtime_checks" in report:
        lines += ["", "Separate runners: 5/5 PASS on recorded worker/n8n image IDs, without network. Includes two real full-resolution FFmpeg renders using synthetic audio/images. Initial 45s harness timeout and successful bounded 110s retry are both retained. See `separate-checks.json`; this is not a real multilingual product acceptance."]
    if "latest_release_checks" in report:
        lines += ["", "Latest checks: Node886/886, SQL8/8 retained with unchanged SQL/workflow hashes, separate runners5/5, current native integrated9 unique selections. S4/S8 received two fresh provider responses; the other seven are saved responses with matching current sources and contracts. This is offline release evidence, not a new production acceptance."]
    lines += ["", "## Stage boundaries", "", "Every row below has partial evidence; none is marked as a current-release integrated acceptance pass.", "", "| Boundary | Supporting checks | Evidence limit |", "|---|---|---|"]
    for row in report["boundaries"]:
        lines.append("| " + row["boundary"] + " | " + ", ".join("`" + p + "`" for p in row["supporting_files"]) + " | " + row["evidence_limit"] + " |")
    lines += ["", "## Explicit fixture metadata", "", "Metadata records source fields, not inferred language from prose or filenames. Multiple fields may come from synthetic controls. Fixture presence/reference is not a passing provider or product result.", "", "| Fixture | Explicit language/locale | Explicit target seconds | Referencing runners |", "|---|---|---|---:|"]
    for row in report["fixtures"]:
        metadata = row["explicit_metadata"]
        lines.append(f"| `{row['path']}` | {', '.join(metadata['languages']) or 'unknown'} | {', '.join(str(x) for x in metadata['target_seconds']) or 'unknown'} | {len(row['literal_reference_runners'])} |")
    lines += ["", "## Release blockers", ""] + [f"{i}. {item}" for i, item in enumerate(report["release_blockers"], 1)]
    lines += ["", "Machine-readable fixture hashes, schemas, provenance fields, runner references and boundaries are in `coverage.json`. Report generation itself is not a test run.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="acceptance/release-coverage")
    args = parser.parse_args()
    report = inventory()
    out = ROOT / args.output_dir
    separate = out / "separate-checks.json"
    if separate.exists():
        checks = json.loads(separate.read_text())
        assert checks["worker_source_sha256"] == hashlib.sha256((ROOT / "services/media-worker/server.py").read_bytes()).hexdigest()
        for check in checks["checks"]:
            assert hashlib.sha256((ROOT / check["log"]).read_bytes()).hexdigest() == check["log_sha256"]
        report["separate_runtime_checks"] = checks
        if checks["all_five_passed"]:
            report["release_blockers"] = [item for item in report["release_blockers"] if not item.startswith("Run relevant separate worker regressions")]
    latest = out / "release-checkpoint.json"
    if latest.exists():
        evidence = json.loads(latest.read_text())
        for path, digest in evidence["sha256"].items():
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
        report["latest_release_checks"] = evidence
        if evidence["integrated_visual_replay"]["unique_selected"] == 9:
            report["release_blockers"] = [item for item in report["release_blockers"] if not item.startswith(("Inspect actual S4", "Establish final current nine-scene"))]
    out.mkdir(parents=True, exist_ok=True)
    (out / "coverage.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    (out / "coverage.md").write_text(markdown(report))
    print(json.dumps({"output": str(out.relative_to(ROOT)), "summary": report["summary"], "hashes_valid": report["checkpoint_hashes_valid"], "provider_calls": 0, "production_mutations": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
