#!/usr/bin/env python3
"""
Automated Query + Verifier generation pipeline.

Uses LLM API (OpenAI-compatible) to batch-generate OSWorld-style tasks
with programmatic verifiers. No human annotation required.

Usage:
    python generate_tasks.py \
        --domain os \
        --num_tasks 100 \
        --output_dir ./generated_tasks \
        --api_base https://api.openai.com/v1 \
        --model gpt-4o

    # Generate for all domains:
    python generate_tasks.py \
        --domain all \
        --num_tasks 50 \
        --output_dir ./generated_tasks
"""

import argparse
import json
import os
import uuid
import sys
import time
import logging
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

try:
    import openai
except ImportError:
    logger.error("openai package not installed. Run: pip install openai")
    sys.exit(1)

from verifier_templates import ALL_TEMPLATES, VERIFIER_PATTERNS


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert at designing computer-use evaluation tasks for Ubuntu Linux.

Your job is to generate tasks that:
1. Are realistic desktop operations a user would actually perform
2. Can be verified PROGRAMMATICALLY (no visual inspection needed)
3. Have a clear, deterministic success condition
4. Cover diverse difficulty levels (easy / medium / hard)

For each task you produce a JSON object with these fields:
- "instruction": natural language task description (what the user wants done)
- "difficulty": "easy" | "medium" | "hard"
- "config": list of init steps to set up the environment before the agent starts
- "evaluator": the verification logic (must use ONLY the patterns provided below)
- "postconfig": (optional) steps to run after agent finishes, before verification

CRITICAL RULES:
- The evaluator must be deterministic. Use shell commands, file checks, gsettings reads, etc.
- Do NOT use LLM-as-Judge or screenshot comparison.
- Verifier commands must work on a default Ubuntu 24.04 GNOME desktop.
- All file paths should be under /home/user/.
- Config commands must create a clean, reproducible initial state.
- The task must be completable via GUI interaction (clicking, typing, keyboard shortcuts).
- Do NOT generate tasks that require internet access or external services.
"""


def build_generation_prompt(domain: str, category: dict, num_tasks: int) -> str:
    """Build the user prompt for a specific domain + category."""

    template = ALL_TEMPLATES[domain]

    examples_json = ""
    if category.get("examples"):
        examples_json = json.dumps(category["examples"][:2], indent=2, ensure_ascii=False)

    return f"""Generate {num_tasks} diverse tasks for the following domain and category.

## Domain: {template['domain']}
{template['description']}

## Category: {category['name']}
{category['description']}

## Verifier strategy for this category:
{category['verifier_strategy']}

{VERIFIER_PATTERNS}

{"## Example tasks (follow this pattern):" + chr(10) + examples_json if examples_json else ""}

## Output format
Return a JSON array of {num_tasks} task objects. Each object must have:
```json
{{
  "instruction": "...",
  "difficulty": "easy|medium|hard",
  "config": [ ... ],
  "evaluator": {{
    "postconfig": [ ... ],
    "func": "...",
    "result": {{ ... }},
    "expected": {{ ... }}
  }}
}}
```

Requirements:
- Vary the difficulty: ~40% easy, ~40% medium, ~20% hard
- Each task must be unique and non-trivial
- Instructions should be natural and varied (not repetitive templates)
- Config must set up a clean initial state (create needed files, reset settings, etc.)
- Evaluator must be self-contained and deterministic
- For file-based tasks, create the necessary seed files in config
- Use realistic file names, content, and scenarios
- Make sure the verifier actually tests what the instruction asks

Return ONLY the JSON array, no other text.
"""


def build_batch_generation_prompt(domain: str, num_tasks: int) -> str:
    """Build prompt to generate tasks across all categories of a domain."""

    template = ALL_TEMPLATES[domain]
    categories_desc = "\n".join(
        f"- **{c['name']}**: {c['description']} (verify via: {c['verifier_strategy']})"
        for c in template["task_categories"]
    )

    all_examples = []
    for cat in template["task_categories"]:
        all_examples.extend(cat.get("examples", [])[:1])
    examples_json = json.dumps(all_examples[:3], indent=2, ensure_ascii=False) if all_examples else ""

    return f"""Generate {num_tasks} diverse tasks for Ubuntu desktop operations.

## Domain: {template['domain']}
{template['description']}

## Available categories (distribute tasks across ALL of them):
{categories_desc}

{VERIFIER_PATTERNS}

{"## Example tasks (follow these patterns):" + chr(10) + examples_json if examples_json else ""}

## Output format
Return a JSON array of {num_tasks} task objects. Each object must have:
```json
{{
  "instruction": "...",
  "difficulty": "easy|medium|hard",
  "category": "<one of the categories above>",
  "config": [ ... ],
  "evaluator": {{
    "postconfig": [ ... ],
    "func": "...",
    "result": {{ ... }},
    "expected": {{ ... }}
  }}
}}
```

Requirements:
- Distribute tasks roughly evenly across categories
- ~40% easy, ~40% medium, ~20% hard
- Each task must be unique, realistic, and non-trivial
- Instructions should read naturally (not like templates)
- Config must create a clean, reproducible initial state
- Evaluator must be deterministic (shell commands, file checks, etc.)
- ALL file paths under /home/user/
- Tasks must be completable via GUI only (no terminal access for the agent)
- For "os" domain: the agent interacts with Files (Nautilus), Settings, or Terminal app via GUI

Return ONLY the JSON array, no other text.
"""


# ---------------------------------------------------------------------------
# LLM API interaction
# ---------------------------------------------------------------------------

def call_llm(
    prompt: str,
    system_prompt: str = SYSTEM_PROMPT,
    model: str = "gpt-4o",
    api_base: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.8,
    max_retries: int = 3,
) -> str:
    """Call the LLM API and return raw text response."""

    client_kwargs = {}
    if api_base:
        client_kwargs["base_url"] = api_base
    if api_key:
        client_kwargs["api_key"] = api_key
    elif os.environ.get("OPENAI_API_KEY"):
        client_kwargs["api_key"] = os.environ["OPENAI_API_KEY"]
    else:
        raise ValueError("No API key provided. Set OPENAI_API_KEY or pass --api_key.")

    client = openai.OpenAI(**client_kwargs)

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=16384,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"API call failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise


def parse_llm_response(response_text: str) -> List[Dict]:
    """Extract JSON array from LLM response (handles markdown code fences)."""

    text = response_text.strip()

    if text.startswith("```"):
        lines = text.split("\n")
        start = 1
        end = len(lines) - 1
        if lines[-1].strip() == "```":
            end = len(lines) - 1
        text = "\n".join(lines[start:end])

    text = text.strip()
    if text.startswith("```"):
        text = text[text.index("\n")+1:]
    if text.endswith("```"):
        text = text[:text.rindex("```")]

    bracket_start = text.find("[")
    bracket_end = text.rfind("]")
    if bracket_start != -1 and bracket_end != -1:
        text = text[bracket_start:bracket_end + 1]

    return json.loads(text)


# ---------------------------------------------------------------------------
# Task post-processing and validation
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


def validate_task(task: Dict, domain: str) -> List[str]:
    """Validate a generated task and return list of issues (empty = valid)."""
    issues = []

    if not task.get("instruction"):
        issues.append("Missing instruction")

    if not task.get("evaluator"):
        issues.append("Missing evaluator")
        return issues

    ev = task["evaluator"]

    func = ev.get("func")
    if isinstance(func, str) and func not in VALID_FUNCS:
        issues.append(f"Unknown evaluator func: {func}")

    result = ev.get("result", {})
    rtype = result.get("type", "")
    if rtype and rtype not in VALID_RESULT_TYPES:
        issues.append(f"Unknown result type: {rtype}")

    if not ev.get("expected") and func != "infeasible":
        issues.append("Missing expected in evaluator")

    config = task.get("config", [])
    for i, step in enumerate(config):
        if not step.get("type"):
            issues.append(f"Config step {i} missing type")

    return issues


def enrich_task(task: Dict, domain: str) -> Dict:
    """Add OSWorld-standard fields to a generated task."""
    template = ALL_TEMPLATES[domain]

    enriched = {
        "id": str(uuid.uuid4()),
        "snapshot": template["snapshot"],
        "instruction": task["instruction"],
        "source": "auto_generated",
        "config": task.get("config", []),
        "trajectory": "trajectories/",
        "related_apps": template["related_apps"],
        "evaluator": task["evaluator"],
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low",
        "_meta": {
            "difficulty": task.get("difficulty", "medium"),
            "category": task.get("category", "unknown"),
            "domain": domain,
            "generated": True,
        },
    }

    return enriched


# ---------------------------------------------------------------------------
# Main generation pipeline
# ---------------------------------------------------------------------------

def generate_for_domain(
    domain: str,
    num_tasks: int,
    model: str,
    api_base: Optional[str],
    api_key: Optional[str],
    batch_size: int = 20,
) -> List[Dict]:
    """Generate tasks for a single domain."""

    logger.info(f"Generating {num_tasks} tasks for domain: {domain}")
    all_tasks = []
    remaining = num_tasks

    while remaining > 0:
        batch = min(batch_size, remaining)
        prompt = build_batch_generation_prompt(domain, batch)

        try:
            response = call_llm(
                prompt, model=model, api_base=api_base, api_key=api_key
            )
            tasks = parse_llm_response(response)
        except Exception as e:
            logger.error(f"Failed to generate batch for {domain}: {e}")
            continue

        valid_count = 0
        for task in tasks:
            issues = validate_task(task, domain)
            if issues:
                logger.warning(f"Invalid task skipped: {issues}")
                continue
            enriched = enrich_task(task, domain)
            all_tasks.append(enriched)
            valid_count += 1

        logger.info(f"  Batch: {valid_count}/{len(tasks)} valid tasks")
        remaining -= valid_count

        if valid_count == 0:
            logger.warning(f"  Zero valid tasks in batch, retrying...")

    return all_tasks[:num_tasks]


def main():
    parser = argparse.ArgumentParser(description="Auto-generate CUA RL tasks with verifiers")
    parser.add_argument("--domain", type=str, default="os",
                        help="Domain to generate for (os, libreoffice_calc, chrome, ..., or 'all')")
    parser.add_argument("--num_tasks", type=int, default=50,
                        help="Number of tasks to generate per domain")
    parser.add_argument("--output_dir", type=str, default="./generated_tasks",
                        help="Output directory")
    parser.add_argument("--model", type=str, default="gpt-4o",
                        help="LLM model name")
    parser.add_argument("--api_base", type=str, default=None,
                        help="API base URL (for non-OpenAI endpoints)")
    parser.add_argument("--api_key", type=str, default=None,
                        help="API key (or set OPENAI_API_KEY env var)")
    parser.add_argument("--batch_size", type=int, default=20,
                        help="Number of tasks per LLM call")
    parser.add_argument("--parallel", type=int, default=4,
                        help="Number of parallel API calls (for 'all' mode)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    domains = list(ALL_TEMPLATES.keys()) if args.domain == "all" else [args.domain]

    if args.domain != "all" and args.domain not in ALL_TEMPLATES:
        logger.error(f"Unknown domain: {args.domain}. Available: {list(ALL_TEMPLATES.keys())}")
        sys.exit(1)

    all_results = {}

    if args.domain == "all" and args.parallel > 1:
        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            futures = {
                executor.submit(
                    generate_for_domain, d, args.num_tasks, args.model,
                    args.api_base, args.api_key, args.batch_size
                ): d for d in domains
            }
            for future in as_completed(futures):
                d = futures[future]
                try:
                    tasks = future.result()
                    all_results[d] = tasks
                except Exception as e:
                    logger.error(f"Domain {d} failed: {e}")
    else:
        for d in domains:
            tasks = generate_for_domain(
                d, args.num_tasks, args.model,
                args.api_base, args.api_key, args.batch_size
            )
            all_results[d] = tasks

    # Save results
    total = 0
    for domain, tasks in all_results.items():
        domain_dir = os.path.join(args.output_dir, domain)
        os.makedirs(domain_dir, exist_ok=True)

        for task in tasks:
            task_path = os.path.join(domain_dir, f"{task['id']}.json")
            with open(task_path, "w", encoding="utf-8") as f:
                json.dump(task, f, indent=2, ensure_ascii=False)

        total += len(tasks)
        logger.info(f"Saved {len(tasks)} tasks to {domain_dir}/")

    # Save aggregate file
    all_tasks = []
    for tasks in all_results.values():
        all_tasks.extend(tasks)

    aggregate_path = os.path.join(args.output_dir, "all_tasks.json")
    with open(aggregate_path, "w", encoding="utf-8") as f:
        json.dump(all_tasks, f, indent=2, ensure_ascii=False)

    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info(f"Generation complete!")
    logger.info(f"Total tasks: {total}")
    for domain, tasks in all_results.items():
        diff_dist = {}
        for t in tasks:
            d = t.get("_meta", {}).get("difficulty", "?")
            diff_dist[d] = diff_dist.get(d, 0) + 1
        logger.info(f"  {domain}: {len(tasks)} tasks {diff_dist}")
    logger.info(f"Output: {args.output_dir}")


if __name__ == "__main__":
    main()
