# CUA Task Generator

Automated pipeline to generate RL training tasks (query + verifier) for
desktop GUI agents, targeting OSWorld-compatible Ubuntu environments.

## Architecture

```
                                ┌──────────────────┐
                                │  LLM API         │
                                │  (GPT-4o etc.)   │
                                └────────┬─────────┘
                                         │
    ┌────────────────┐          ┌────────▼─────────┐         ┌─────────────────┐
    │  Verifier       │ ──────▶ │  generate_tasks   │ ──────▶ │  Raw Tasks      │
    │  Templates      │         │  .py              │         │  (JSON)         │
    └────────────────┘          └──────────────────┘         └────────┬────────┘
                                                                      │
                                                             ┌────────▼────────┐
                                                             │  validate_tasks  │
                                                             │  .py             │
                                                             └────────┬────────┘
                                                                      │
                                                    ┌─────────────────┼──────────────────┐
                                                    ▼                 ▼                  ▼
                                            Structurally       Sanity Check        ✗ Rejected
                                            Valid              (verifier fails     (bad format,
                                                               on clean env)       false positive)
                                                    │
                                           ┌────────▼────────┐
                                           │  augment_tasks   │
                                           │  .py             │
                                           └────────┬────────┘
                                                    │
                                    ┌───────────────┼───────────────┐
                                    ▼               ▼               ▼
                            Parameter           Difficulty       Cross-app
                            Variation           Escalation       Composition
                                    │               │               │
                                    └───────────────┼───────────────┘
                                                    ▼
                                          Final Task Pool
                                          (3000-5000 tasks)
```

## Quick Start

```bash
pip install openai

# 1. Generate seed tasks for one domain
python generate_tasks.py \
    --domain os \
    --num_tasks 50 \
    --output_dir ./generated_tasks \
    --model gpt-4o

# 2. Generate for all domains
python generate_tasks.py \
    --domain all \
    --num_tasks 50 \
    --output_dir ./generated_tasks

# 3. Validate (structure only)
python validate_tasks.py \
    --task_dir ./generated_tasks \
    --mode dry_run \
    --report validation_report.json

# 4. Validate (sanity: run verifier commands locally)
python validate_tasks.py \
    --task_dir ./generated_tasks \
    --mode sanity \
    --report sanity_report.json

# 5. Augment: parameter variations (5x per seed)
python augment_tasks.py \
    --seed_dir ./generated_tasks \
    --output_dir ./augmented_tasks \
    --strategy parameter_variation \
    --multiplier 5

# 6. Augment: make tasks harder
python augment_tasks.py \
    --seed_dir ./generated_tasks \
    --output_dir ./harder_tasks \
    --strategy escalation

# 7. Augment: cross-app composition
python augment_tasks.py \
    --seed_dir ./generated_tasks \
    --output_dir ./composed_tasks \
    --strategy composition \
    --multiplier 100
```

## Scaling Plan

Target: 3000-5000 tasks with verifiers.

| Stage | Method | Input | Output |
|-------|--------|-------|--------|
| 1. Seed generation | `generate_tasks.py` | Templates + LLM | ~500 seed tasks |
| 2. Structural validation | `validate_tasks.py --mode dry_run` | 500 seeds | ~450 valid |
| 3. Sanity validation | `validate_tasks.py --mode sanity` | 450 valid | ~400 clean |
| 4. Parameter variation (5x) | `augment_tasks.py --strategy parameter_variation` | 400 seeds | ~2000 tasks |
| 5. Difficulty escalation | `augment_tasks.py --strategy escalation` | 400 seeds | ~400 hard tasks |
| 6. Cross-app composition | `augment_tasks.py --strategy composition` | all seeds | ~200 multi-app |
| 7. Re-validate all | `validate_tasks.py` | ~2600 | ~2400 final |
| 8. Iterate with new categories | Repeat 1-7 | expand templates | 3000-5000 |

## OSWorld Compatibility

Generated tasks follow the OSWorld JSON format:

```json
{
  "id": "uuid",
  "snapshot": "os",
  "instruction": "...",
  "source": "auto_generated",
  "config": [ ... ],
  "trajectory": "trajectories/",
  "related_apps": ["os"],
  "evaluator": {
    "postconfig": [ ... ],
    "func": "check_include_exclude",
    "result": { "type": "vm_command_line", "command": [...] },
    "expected": { "type": "rule", "rules": { ... } }
  }
}
```

## Supported Domains

| Domain | OSWorld App | Key Verifier Patterns |
|--------|------------|----------------------|
| `os` | File manager, Terminal, Settings | `vm_command_line` → `check_include_exclude`, `exact_match` |
| `libreoffice_calc` | LibreOffice Calc | `vm_file` → `compare_table` |
| `libreoffice_writer` | LibreOffice Writer | `vm_file` → `compare_docx_files` |
| `libreoffice_impress` | LibreOffice Impress | `vm_file` → `compare_pptx_files` |
| `chrome` | Google Chrome | CDP / prefs → `exact_match`, `check_json` |
| `vs_code` | VS Code | `vm_command_line` → `is_extension_installed`, `check_json` |
| `gimp` | GIMP | `vm_file` → `compare_images` |
| `thunderbird` | Thunderbird | `vm_file` → `check_thunderbird_prefs` |
| `vlc` | VLC | `vm_file` → config checks |

## Files

| File | Purpose |
|------|---------|
| `verifier_templates.py` | Domain-specific templates with verifier patterns and few-shot examples |
| `generate_tasks.py` | LLM-based seed task generation |
| `validate_tasks.py` | Structural + sanity validation |
| `augment_tasks.py` | Scale up via variation / escalation / composition |
