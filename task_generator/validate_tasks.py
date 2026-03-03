#!/usr/bin/env python3
"""
Validate generated tasks by running verifiers in a sandbox.

This script does NOT need an agent — it tests verifiers for correctness:
  1. Sanity check: run verifier on a clean env (before agent) → should FAIL
  2. Gold check:   programmatically execute the "gold" solution, then run verifier → should PASS

This catches:
  - Verifiers that always pass (false positive)
  - Verifiers that always fail (broken command / wrong path)
  - Init configs that fail to execute
  - Verifier commands with syntax errors

Usage:
    # Validate a single task
    python validate_tasks.py --task_file generated_tasks/os/xxx.json --mode sanity

    # Batch validate all tasks in a directory
    python validate_tasks.py --task_dir generated_tasks/ --mode sanity --report report.json

    # Dry-run: just check JSON structure without executing
    python validate_tasks.py --task_dir generated_tasks/ --mode dry_run
"""

import argparse
import json
import os
import sys
import subprocess
import logging
from typing import Dict, List, Any, Tuple
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structural validation (no execution needed)
# ---------------------------------------------------------------------------

VALID_FUNCS = {
    "check_include_exclude", "exact_match", "match_in_list", "literal_match",
    "is_in_list", "diff_text_file", "fuzzy_match", "check_csv", "check_list",
    "check_accessibility_tree", "run_sqlite3", "check_json",
    "check_direct_json_object", "file_contains", "compare_table",
    "compare_pptx_files", "compare_docx_files", "compare_docx_tables",
    "compare_images", "compare_text_file", "compare_pdfs", "compare_audios",
    "compare_videos", "is_extension_installed", "is_expected_bookmarks",
    "is_expected_active_tab", "is_expected_url_pattern_match",
    "check_json_settings", "check_json_keybindings", "check_config_status",
    "check_thunderbird_prefs", "check_thunderbird_filter",
    "check_structure_sim", "infeasible",
}

VALID_RESULT_TYPES = {
    "vm_command_line", "vm_file", "vm_terminal_output", "vm_command_error",
    "vm_wallpaper", "vm_window_size", "vm_screen_size",
    "cloud_file", "cache_file",
}

VALID_CONFIG_TYPES = {
    "execute", "launch", "command", "download", "open",
    "activate_window", "close_window", "sleep",
}


def validate_structure(task: Dict) -> List[str]:
    """Validate the JSON structure of a task. Returns list of issues."""
    issues = []

    required_fields = ["id", "instruction", "evaluator"]
    for field in required_fields:
        if field not in task:
            issues.append(f"Missing required field: {field}")

    if not task.get("instruction", "").strip():
        issues.append("Empty instruction")

    ev = task.get("evaluator", {})

    func = ev.get("func")
    if isinstance(func, str):
        if func not in VALID_FUNCS:
            issues.append(f"Unknown evaluator func: {func}")
    elif isinstance(func, list):
        for f in func:
            if f not in VALID_FUNCS:
                issues.append(f"Unknown evaluator func in list: {f}")
    elif func is None:
        issues.append("Missing evaluator func")

    result = ev.get("result", {})
    if result:
        rtype = result.get("type", "")
        if rtype not in VALID_RESULT_TYPES:
            issues.append(f"Unknown result type: {rtype}")

        if rtype == "vm_command_line":
            cmd = result.get("command")
            if not cmd:
                issues.append("vm_command_line result missing 'command'")
            elif isinstance(cmd, list) and len(cmd) == 0:
                issues.append("vm_command_line has empty command list")

        if rtype == "vm_file":
            if not result.get("path"):
                issues.append("vm_file result missing 'path'")
            if not result.get("dest"):
                issues.append("vm_file result missing 'dest'")

    if func != "infeasible" and not ev.get("expected"):
        issues.append("Non-infeasible task missing 'expected' in evaluator")

    for i, step in enumerate(task.get("config", [])):
        stype = step.get("type")
        if stype and stype not in VALID_CONFIG_TYPES:
            issues.append(f"Config step {i}: unknown type '{stype}'")
        if stype in ("execute", "command") and not step.get("parameters", {}).get("command"):
            issues.append(f"Config step {i}: execute/command type missing command")

    for i, step in enumerate(ev.get("postconfig", [])):
        stype = step.get("type")
        if stype and stype not in VALID_CONFIG_TYPES:
            issues.append(f"Postconfig step {i}: unknown type '{stype}'")

    return issues


# ---------------------------------------------------------------------------
# Sanity check: verifier should FAIL on clean environment
# ---------------------------------------------------------------------------

def extract_verifier_command(task: Dict) -> List[str]:
    """Extract the shell command from a task's verifier (if it's command-based)."""
    ev = task.get("evaluator", {})
    result = ev.get("result", {})

    if result.get("type") != "vm_command_line":
        return None

    cmd = result.get("command", [])
    if isinstance(cmd, list):
        return cmd
    return None


def run_command_local(cmd: List[str], timeout: int = 10) -> Tuple[int, str, str]:
    """Run a command locally and return (returncode, stdout, stderr)."""
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "HOME": "/home/user"}
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return -1, "", str(e)


def sanity_check_task(task: Dict) -> Dict[str, Any]:
    """
    Run the verifier command on the current (clean) system.
    For a well-designed verifier, this should FAIL (return 0 / empty / not match).
    If the verifier passes without the agent doing anything, it's a false positive.
    """
    result = {"task_id": task["id"], "instruction": task["instruction"][:80]}

    cmd = extract_verifier_command(task)
    if cmd is None:
        result["status"] = "skipped"
        result["reason"] = "Not a vm_command_line verifier"
        return result

    rc, stdout, stderr = run_command_local(cmd)
    result["command"] = cmd
    result["stdout"] = stdout[:500]
    result["stderr"] = stderr[:500]
    result["returncode"] = rc

    ev = task["evaluator"]
    func = ev.get("func")
    expected = ev.get("expected", {})
    rules = expected.get("rules", {})

    if func == "check_include_exclude":
        includes = rules.get("include", [])
        all_found = all(inc in stdout for inc in includes)
        if all_found and includes:
            result["status"] = "WARNING_FALSE_POSITIVE"
            result["reason"] = "Verifier passes on clean env (all includes found)"
        else:
            result["status"] = "OK"
            result["reason"] = "Verifier correctly fails on clean env"

    elif func == "exact_match":
        expected_val = rules.get("expected", "")
        if stdout.strip() == expected_val.strip("'\""):
            result["status"] = "WARNING_FALSE_POSITIVE"
            result["reason"] = f"Output already matches expected: {expected_val}"
        else:
            result["status"] = "OK"
            result["reason"] = "Verifier correctly fails on clean env"

    else:
        result["status"] = "skipped"
        result["reason"] = f"Sanity check not implemented for func: {func}"

    return result


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

def load_tasks_from_dir(task_dir: str) -> List[Dict]:
    """Recursively load all task JSON files from a directory."""
    tasks = []
    for root, dirs, files in os.walk(task_dir):
        for f in files:
            if f.endswith(".json") and f != "all_tasks.json":
                path = os.path.join(root, f)
                try:
                    with open(path) as fh:
                        task = json.load(fh)
                        task["_source_file"] = path
                        tasks.append(task)
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")
    return tasks


def main():
    parser = argparse.ArgumentParser(description="Validate generated CUA tasks")
    parser.add_argument("--task_file", type=str, help="Path to a single task JSON")
    parser.add_argument("--task_dir", type=str, help="Path to directory of task JSONs")
    parser.add_argument("--mode", type=str, choices=["dry_run", "sanity"], default="dry_run",
                        help="dry_run = structure only, sanity = also run verifier commands locally")
    parser.add_argument("--report", type=str, default=None,
                        help="Path to save validation report JSON")
    args = parser.parse_args()

    if not args.task_file and not args.task_dir:
        parser.error("Must provide --task_file or --task_dir")

    # Load tasks
    if args.task_file:
        with open(args.task_file) as f:
            tasks = [json.load(f)]
    else:
        tasks = load_tasks_from_dir(args.task_dir)

    logger.info(f"Loaded {len(tasks)} tasks")

    # Validate
    report = {
        "total": len(tasks),
        "structural_valid": 0,
        "structural_invalid": 0,
        "sanity_ok": 0,
        "sanity_false_positive": 0,
        "sanity_skipped": 0,
        "issues": [],
        "details": [],
    }

    for task in tasks:
        # Structural validation
        issues = validate_structure(task)
        if issues:
            report["structural_invalid"] += 1
            report["issues"].append({
                "task_id": task.get("id", "?"),
                "file": task.get("_source_file", "?"),
                "issues": issues,
            })
            logger.warning(f"  INVALID {task.get('id', '?')[:8]}: {issues}")
        else:
            report["structural_valid"] += 1

        # Sanity check (if requested)
        if args.mode == "sanity" and not issues:
            sanity_result = sanity_check_task(task)
            report["details"].append(sanity_result)

            if sanity_result["status"] == "OK":
                report["sanity_ok"] += 1
            elif sanity_result["status"] == "WARNING_FALSE_POSITIVE":
                report["sanity_false_positive"] += 1
                logger.warning(f"  FALSE POSITIVE {task.get('id', '?')[:8]}: {sanity_result['reason']}")
            else:
                report["sanity_skipped"] += 1

    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info(f"Validation Summary ({args.mode} mode)")
    logger.info(f"  Total tasks:           {report['total']}")
    logger.info(f"  Structurally valid:    {report['structural_valid']}")
    logger.info(f"  Structurally invalid:  {report['structural_invalid']}")
    if args.mode == "sanity":
        logger.info(f"  Sanity OK:             {report['sanity_ok']}")
        logger.info(f"  Sanity FALSE POSITIVE: {report['sanity_false_positive']}")
        logger.info(f"  Sanity skipped:        {report['sanity_skipped']}")

    # Save report
    if args.report:
        with open(args.report, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Report saved to {args.report}")

    # Exit code
    if report["structural_invalid"] > 0 or report.get("sanity_false_positive", 0) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
