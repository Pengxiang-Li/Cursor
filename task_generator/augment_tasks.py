#!/usr/bin/env python3
"""
Task augmentation pipeline: take validated seed tasks and use LLM to
generate variations at scale.

Strategies:
  1. Parameter variation: same task structure, different file names/values/paths
  2. Instruction rephrasing: same task, different natural language
  3. Difficulty escalation: add constraints or combine with other tasks
  4. Cross-app composition: combine tasks from different apps into workflows

Usage:
    python augment_tasks.py \
        --seed_dir generated_tasks/ \
        --output_dir augmented_tasks/ \
        --strategy parameter_variation \
        --multiplier 5 \
        --model gpt-4o
"""

import argparse
import json
import os
import uuid
import copy
import sys
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

try:
    import openai
except ImportError:
    logger.error("openai package not installed. Run: pip install openai")
    sys.exit(1)


VARIATION_SYSTEM_PROMPT = """You are an expert at creating variations of computer-use tasks.
Given a seed task (instruction + verifier), create variations that:
1. Change the specific parameters (file names, values, paths) but keep the same structure
2. Each variation must have its own valid config (init state) and evaluator (verifier)
3. The verifier must be deterministic and test the exact task
4. Variations should feel natural, not like find-and-replace
"""


def build_variation_prompt(seed_task: Dict, num_variations: int) -> str:
    seed_json = json.dumps({
        "instruction": seed_task["instruction"],
        "config": seed_task.get("config", []),
        "evaluator": seed_task.get("evaluator", {}),
    }, indent=2, ensure_ascii=False)

    return f"""Given this seed task, generate {num_variations} parameter variations.

## Seed task:
```json
{seed_json}
```

## Rules:
- Change file names, directory names, text content, settings values, etc.
- Keep the SAME evaluator function and result type
- Each variation must be self-contained with its own config and evaluator
- Do NOT change the fundamental task type (e.g., if seed is "create directory", variations should also be "create directory" but with different names/paths)
- Make instructions sound natural and diverse

## Output:
Return a JSON array of {num_variations} task objects, each with:
- "instruction": varied natural language
- "config": init steps for this variation
- "evaluator": verifier for this variation

Return ONLY the JSON array.
"""


COMPOSITION_SYSTEM_PROMPT = """You are an expert at composing multi-step computer-use tasks.
Given two or more seed tasks from different apps, combine them into a single
multi-step workflow task. The combined task must have a verifier that checks
all parts were completed correctly."""


def build_composition_prompt(seed_tasks: List[Dict]) -> str:
    seeds = []
    for t in seed_tasks:
        seeds.append({
            "domain": t.get("_meta", {}).get("domain", t.get("related_apps", ["?"])[0]),
            "instruction": t["instruction"],
            "config": t.get("config", []),
            "evaluator": t.get("evaluator", {}),
        })

    return f"""Combine these tasks into a single multi-step workflow:

{json.dumps(seeds, indent=2, ensure_ascii=False)}

## Rules:
- The combined instruction should describe the full workflow naturally
- Config should set up initial state for ALL parts
- Evaluator should verify ALL parts completed (use check_include_exclude with multiple includes, or use a func list)
- The workflow should make logical sense (not just concatenation)
- related_apps should list all involved apps

## Output:
Return a single JSON object with: instruction, config, evaluator, related_apps

Return ONLY the JSON object.
"""


ESCALATION_SYSTEM_PROMPT = """You are an expert at making computer-use tasks harder.
Given a task, create a harder version by adding constraints, conditions,
or requiring more steps. The verifier must still be deterministic."""


def build_escalation_prompt(seed_task: Dict) -> str:
    seed_json = json.dumps({
        "instruction": seed_task["instruction"],
        "config": seed_task.get("config", []),
        "evaluator": seed_task.get("evaluator", {}),
    }, indent=2, ensure_ascii=False)

    return f"""Make this task harder. Strategies:
- Add a precondition ("if X then do Y, otherwise do Z")
- Add multiple objectives ("do X AND ALSO Y")
- Add constraints ("do X but without using the menu")
- Require more steps or precision

## Seed task:
```json
{seed_json}
```

## Rules:
- The harder task must still be verifiable programmatically
- Update the config and evaluator accordingly
- Set difficulty to "hard" or "expert"

## Output:
Return a JSON object with: instruction, difficulty, config, evaluator

Return ONLY the JSON object.
"""


def call_llm(prompt, system_prompt, model, api_base, api_key, temperature=0.8):
    client_kwargs = {}
    if api_base:
        client_kwargs["base_url"] = api_base
    if api_key:
        client_kwargs["api_key"] = api_key
    elif os.environ.get("OPENAI_API_KEY"):
        client_kwargs["api_key"] = os.environ["OPENAI_API_KEY"]
    else:
        raise ValueError("No API key. Set OPENAI_API_KEY or pass --api_key.")

    client = openai.OpenAI(**client_kwargs)
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


def parse_json_response(text: str):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
    if text.endswith("```"):
        text = text[:text.rindex("```")]
    text = text.strip()

    if text.startswith("["):
        return json.loads(text)
    elif text.startswith("{"):
        return json.loads(text)

    bracket = text.find("[")
    brace = text.find("{")
    if bracket != -1 and (brace == -1 or bracket < brace):
        return json.loads(text[bracket:text.rfind("]") + 1])
    elif brace != -1:
        return json.loads(text[brace:text.rfind("}") + 1])

    raise ValueError(f"Cannot parse JSON from response: {text[:200]}")


def load_tasks(path: str) -> List[Dict]:
    tasks = []
    if os.path.isfile(path):
        with open(path) as f:
            data = json.load(f)
            if isinstance(data, list):
                tasks = data
            else:
                tasks = [data]
    else:
        for root, _, files in os.walk(path):
            for f in files:
                if f.endswith(".json") and f != "all_tasks.json":
                    fp = os.path.join(root, f)
                    try:
                        with open(fp) as fh:
                            tasks.append(json.load(fh))
                    except Exception:
                        pass
    return tasks


def enrich_augmented(task: Dict, seed: Dict, strategy: str) -> Dict:
    """Add standard fields to an augmented task."""
    return {
        "id": str(uuid.uuid4()),
        "snapshot": seed.get("snapshot", "os"),
        "instruction": task.get("instruction", ""),
        "source": f"augmented_{strategy}",
        "config": task.get("config", []),
        "trajectory": "trajectories/",
        "related_apps": task.get("related_apps", seed.get("related_apps", [])),
        "evaluator": task.get("evaluator", {}),
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low",
        "_meta": {
            "difficulty": task.get("difficulty", "medium"),
            "domain": seed.get("_meta", {}).get("domain", "unknown"),
            "strategy": strategy,
            "seed_id": seed.get("id", "?"),
            "generated": True,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Augment CUA tasks")
    parser.add_argument("--seed_dir", type=str, required=True, help="Directory of seed tasks")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory")
    parser.add_argument("--strategy", type=str, default="parameter_variation",
                        choices=["parameter_variation", "escalation", "composition"],
                        help="Augmentation strategy")
    parser.add_argument("--multiplier", type=int, default=5,
                        help="How many variations per seed task")
    parser.add_argument("--model", type=str, default="gpt-4o")
    parser.add_argument("--api_base", type=str, default=None)
    parser.add_argument("--api_key", type=str, default=None)
    parser.add_argument("--max_seeds", type=int, default=None,
                        help="Max number of seed tasks to augment")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    seeds = load_tasks(args.seed_dir)
    if args.max_seeds:
        seeds = seeds[:args.max_seeds]
    logger.info(f"Loaded {len(seeds)} seed tasks, strategy: {args.strategy}")

    all_augmented = []

    if args.strategy == "parameter_variation":
        for i, seed in enumerate(seeds):
            logger.info(f"[{i+1}/{len(seeds)}] Augmenting: {seed.get('instruction', '?')[:60]}")
            try:
                prompt = build_variation_prompt(seed, args.multiplier)
                response = call_llm(prompt, VARIATION_SYSTEM_PROMPT,
                                    args.model, args.api_base, args.api_key)
                variations = parse_json_response(response)
                if isinstance(variations, dict):
                    variations = [variations]

                for v in variations:
                    augmented = enrich_augmented(v, seed, "parameter_variation")
                    all_augmented.append(augmented)

                logger.info(f"  Generated {len(variations)} variations")
            except Exception as e:
                logger.warning(f"  Failed: {e}")

    elif args.strategy == "escalation":
        for i, seed in enumerate(seeds):
            logger.info(f"[{i+1}/{len(seeds)}] Escalating: {seed.get('instruction', '?')[:60]}")
            try:
                prompt = build_escalation_prompt(seed)
                response = call_llm(prompt, ESCALATION_SYSTEM_PROMPT,
                                    args.model, args.api_base, args.api_key)
                harder = parse_json_response(response)
                if isinstance(harder, list):
                    harder = harder[0]

                augmented = enrich_augmented(harder, seed, "escalation")
                all_augmented.append(augmented)
                logger.info(f"  Generated 1 harder variant")
            except Exception as e:
                logger.warning(f"  Failed: {e}")

    elif args.strategy == "composition":
        import random
        domains = {}
        for s in seeds:
            d = s.get("_meta", {}).get("domain", "unknown")
            domains.setdefault(d, []).append(s)

        domain_keys = [k for k in domains if len(domains[k]) >= 2]
        num_compositions = min(len(seeds) // 2, args.multiplier * len(seeds))

        for i in range(num_compositions):
            picked_domains = random.sample(domain_keys, min(2, len(domain_keys)))
            picked_tasks = [random.choice(domains[d]) for d in picked_domains]

            logger.info(f"[{i+1}/{num_compositions}] Composing from {picked_domains}")
            try:
                prompt = build_composition_prompt(picked_tasks)
                response = call_llm(prompt, COMPOSITION_SYSTEM_PROMPT,
                                    args.model, args.api_base, args.api_key)
                composed = parse_json_response(response)
                if isinstance(composed, list):
                    composed = composed[0]

                augmented = enrich_augmented(composed, picked_tasks[0], "composition")
                augmented["snapshot"] = "multi_apps"
                augmented["related_apps"] = composed.get("related_apps", [])
                all_augmented.append(augmented)
                logger.info(f"  Generated 1 composed task")
            except Exception as e:
                logger.warning(f"  Failed: {e}")

    # Save
    for task in all_augmented:
        domain = task.get("_meta", {}).get("domain", "unknown")
        domain_dir = os.path.join(args.output_dir, domain)
        os.makedirs(domain_dir, exist_ok=True)
        path = os.path.join(domain_dir, f"{task['id']}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(task, f, indent=2, ensure_ascii=False)

    aggregate_path = os.path.join(args.output_dir, "all_augmented.json")
    with open(aggregate_path, "w", encoding="utf-8") as f:
        json.dump(all_augmented, f, indent=2, ensure_ascii=False)

    logger.info(f"\nAugmentation complete! Generated {len(all_augmented)} tasks → {args.output_dir}")


if __name__ == "__main__":
    main()
