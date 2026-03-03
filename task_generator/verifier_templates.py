"""
Verifier templates for each OSWorld app domain.

Each template defines:
  - What kinds of tasks are natural for this app
  - How to build the init config (setup)
  - How to build the evaluator (verify)
  - Few-shot examples for the LLM

These templates are designed to produce tasks whose verification is
*deterministic and programmatic* (no LLM-as-Judge), because RL reward
signals must be precise.
"""

# ---------------------------------------------------------------------------
# Domain: os (file management, system settings, terminal)
# Verifier pattern: vm_command_line → check_include_exclude / exact_match
# ---------------------------------------------------------------------------
OS_TEMPLATE = {
    "domain": "os",
    "snapshot": "os",
    "related_apps": ["os"],
    "description": "File management, shell operations, and GNOME system settings on Ubuntu.",
    "task_categories": [
        {
            "name": "file_management",
            "description": "Create, move, copy, rename, delete files and directories",
            "verifier_strategy": "vm_command_line → check_include_exclude or exact_match",
            "examples": [
                {
                    "instruction": "Create a directory called 'projects' in ~/Documents and inside it create three empty files: README.md, main.py, and requirements.txt",
                    "init_config": [
                        {"type": "execute", "parameters": {"command": ["bash", "-c", "rm -rf /home/user/Documents/projects"]}}
                    ],
                    "evaluator": {
                        "func": "check_include_exclude",
                        "result": {
                            "type": "vm_command_line",
                            "command": ["bash", "-c", "ls -1 /home/user/Documents/projects/ 2>/dev/null | sort"]
                        },
                        "expected": {
                            "type": "rule",
                            "rules": {"include": ["README.md", "main.py", "requirements.txt"], "exclude": []}
                        }
                    }
                },
                {
                    "instruction": "Find all .log files in /var/log that are larger than 1MB and copy them to ~/Desktop/large_logs/",
                    "init_config": [
                        {"type": "execute", "parameters": {"command": ["bash", "-c", "mkdir -p /home/user/Desktop/large_logs"]}}
                    ],
                    "evaluator": {
                        "func": "check_include_exclude",
                        "result": {
                            "type": "vm_command_line",
                            "command": ["bash", "-c", "ls /home/user/Desktop/large_logs/ 2>/dev/null | head -20"]
                        },
                        "expected": {
                            "type": "rule",
                            "rules": {"include": [".log"], "exclude": []}
                        }
                    }
                },
            ],
        },
        {
            "name": "file_content",
            "description": "Create files with specific content, edit text files, search and replace",
            "verifier_strategy": "vm_command_line → check_include_exclude",
            "examples": [
                {
                    "instruction": "Create a file ~/notes.txt containing exactly the text 'Hello World' on the first line and 'Goodbye World' on the second line.",
                    "init_config": [
                        {"type": "execute", "parameters": {"command": ["bash", "-c", "rm -f /home/user/notes.txt"]}}
                    ],
                    "evaluator": {
                        "func": "check_include_exclude",
                        "result": {
                            "type": "vm_command_line",
                            "command": ["bash", "-c", "cat /home/user/notes.txt 2>/dev/null"]
                        },
                        "expected": {
                            "type": "rule",
                            "rules": {"include": ["Hello World", "Goodbye World"], "exclude": []}
                        }
                    }
                },
            ],
        },
        {
            "name": "system_settings",
            "description": "Change GNOME desktop settings via GUI (wallpaper, theme, fonts, etc.)",
            "verifier_strategy": "vm_command_line (gsettings/dconf) → exact_match or check_include_exclude",
            "examples": [
                {
                    "instruction": "Change the GNOME desktop to use dark mode (dark theme).",
                    "init_config": [
                        {"type": "execute", "parameters": {"command": ["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", "default"]}}
                    ],
                    "evaluator": {
                        "func": "exact_match",
                        "result": {
                            "type": "vm_command_line",
                            "command": ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"]
                        },
                        "expected": {
                            "type": "rule",
                            "rules": {"expected": "'prefer-dark'"}
                        }
                    }
                },
            ],
        },
        {
            "name": "permissions_ownership",
            "description": "Change file permissions, ownership, create symlinks",
            "verifier_strategy": "vm_command_line → check_include_exclude",
            "examples": [
                {
                    "instruction": "Make the file ~/script.sh executable for the owner.",
                    "init_config": [
                        {"type": "execute", "parameters": {"command": ["bash", "-c", "echo '#!/bin/bash' > /home/user/script.sh && chmod 644 /home/user/script.sh"]}}
                    ],
                    "evaluator": {
                        "func": "check_include_exclude",
                        "result": {
                            "type": "vm_command_line",
                            "command": ["bash", "-c", "stat -c '%a' /home/user/script.sh"]
                        },
                        "expected": {
                            "type": "rule",
                            "rules": {"include": ["7"], "exclude": []}
                        }
                    }
                },
            ],
        },
        {
            "name": "archive_compression",
            "description": "Create or extract tar/zip/gz archives",
            "verifier_strategy": "vm_command_line → check_include_exclude",
            "examples": [],
        },
        {
            "name": "process_management",
            "description": "Kill processes, manage services, check system info",
            "verifier_strategy": "vm_command_line → check_include_exclude",
            "examples": [],
        },
    ],
}

# ---------------------------------------------------------------------------
# Domain: libreoffice_calc
# Verifier pattern: vm_file → compare_table
# ---------------------------------------------------------------------------
CALC_TEMPLATE = {
    "domain": "libreoffice_calc",
    "snapshot": "libreoffice_calc",
    "related_apps": ["libreoffice calc"],
    "description": "Spreadsheet tasks in LibreOffice Calc: formulas, formatting, sorting, filtering, charts.",
    "task_categories": [
        {
            "name": "formula_computation",
            "description": "Enter formulas (SUM, AVERAGE, IF, VLOOKUP, etc.), compute results",
            "verifier_strategy": "vm_file (.xlsx) → compare_table (sheet_data)",
            "examples": [],
        },
        {
            "name": "formatting",
            "description": "Cell formatting: colors, borders, fonts, number formats, conditional formatting",
            "verifier_strategy": "vm_file (.xlsx) → compare_table (sheet_data + sheet_format)",
            "examples": [],
        },
        {
            "name": "data_manipulation",
            "description": "Sort, filter, remove duplicates, data validation, pivot-like operations",
            "verifier_strategy": "vm_file (.xlsx) → compare_table (sheet_data)",
            "examples": [],
        },
        {
            "name": "chart_creation",
            "description": "Create charts from data (bar, line, pie, etc.)",
            "verifier_strategy": "vm_file (.xlsx) → compare_table (sheet_chart)",
            "examples": [],
        },
    ],
}

# ---------------------------------------------------------------------------
# Domain: libreoffice_writer
# Verifier pattern: vm_file → compare_docx_files
# ---------------------------------------------------------------------------
WRITER_TEMPLATE = {
    "domain": "libreoffice_writer",
    "snapshot": "libreoffice_writer",
    "related_apps": ["libreoffice writer"],
    "description": "Document editing in LibreOffice Writer: text formatting, tables, headers/footers, styles.",
    "task_categories": [
        {
            "name": "text_editing",
            "description": "Insert/edit text, find and replace, spell check",
            "verifier_strategy": "vm_file (.docx) → compare_docx_files",
            "examples": [],
        },
        {
            "name": "formatting",
            "description": "Font size/style, paragraph alignment, line spacing, page margins",
            "verifier_strategy": "vm_file (.docx) → compare_docx_files",
            "examples": [],
        },
        {
            "name": "tables",
            "description": "Insert and format tables in documents",
            "verifier_strategy": "vm_file (.docx) → compare_docx_tables",
            "examples": [],
        },
        {
            "name": "export",
            "description": "Export to PDF, change file format",
            "verifier_strategy": "vm_file (.pdf) → compare_pdfs",
            "examples": [],
        },
    ],
}

# ---------------------------------------------------------------------------
# Domain: libreoffice_impress
# Verifier pattern: vm_file → compare_pptx_files
# ---------------------------------------------------------------------------
IMPRESS_TEMPLATE = {
    "domain": "libreoffice_impress",
    "snapshot": "libreoffice_impress",
    "related_apps": ["libreoffice impress"],
    "description": "Presentation tasks in LibreOffice Impress: slides, layouts, transitions, shapes.",
    "task_categories": [
        {
            "name": "slide_content",
            "description": "Add/edit text in slides, insert shapes, images",
            "verifier_strategy": "vm_file (.pptx) → compare_pptx_files",
            "examples": [],
        },
        {
            "name": "slide_management",
            "description": "Add/delete/reorder slides, change layouts",
            "verifier_strategy": "vm_file (.pptx) → compare_pptx_files",
            "examples": [],
        },
        {
            "name": "design",
            "description": "Apply themes, change backgrounds, animations, transitions",
            "verifier_strategy": "vm_file (.pptx) → compare_pptx_files",
            "examples": [],
        },
    ],
}

# ---------------------------------------------------------------------------
# Domain: chrome
# Verifier pattern: vm_command_line (chrome settings/prefs) → exact_match / check_json
# ---------------------------------------------------------------------------
CHROME_TEMPLATE = {
    "domain": "chrome",
    "snapshot": "chrome",
    "related_apps": ["chrome"],
    "description": "Chrome browser tasks: settings, bookmarks, extensions, tabs, downloads.",
    "task_categories": [
        {
            "name": "browser_settings",
            "description": "Change Chrome settings (privacy, homepage, default search, appearance)",
            "verifier_strategy": "vm_command_line or chrome prefs → exact_match / check_json",
            "examples": [],
        },
        {
            "name": "bookmarks",
            "description": "Add, organize, delete bookmarks",
            "verifier_strategy": "chrome bookmarks JSON → is_expected_bookmarks",
            "examples": [],
        },
        {
            "name": "tab_management",
            "description": "Open, close, pin, group tabs",
            "verifier_strategy": "chrome CDP → is_expected_tabs / is_expected_active_tab",
            "examples": [],
        },
        {
            "name": "download_navigation",
            "description": "Navigate to URLs, download files, fill forms",
            "verifier_strategy": "vm_file (downloaded) or vm_command_line → check_include_exclude",
            "examples": [],
        },
    ],
}

# ---------------------------------------------------------------------------
# Domain: vs_code
# Verifier pattern: vm_command_line → check_include_exclude / is_extension_installed
# ---------------------------------------------------------------------------
VSCODE_TEMPLATE = {
    "domain": "vs_code",
    "snapshot": "vscode",
    "related_apps": ["vscode"],
    "description": "VS Code tasks: editing, extensions, settings, terminal, git operations.",
    "task_categories": [
        {
            "name": "file_editing",
            "description": "Open, edit, save files in VS Code",
            "verifier_strategy": "vm_file → diff_text_file or check_include_exclude on file content",
            "examples": [],
        },
        {
            "name": "extensions",
            "description": "Install, uninstall, configure extensions",
            "verifier_strategy": "vm_command_line (code --list-extensions) → is_extension_installed",
            "examples": [],
        },
        {
            "name": "settings",
            "description": "Change VS Code settings (theme, font size, keybindings)",
            "verifier_strategy": "vm_file (settings.json) → check_json",
            "examples": [],
        },
    ],
}

# ---------------------------------------------------------------------------
# Domain: gimp
# Verifier pattern: vm_file (image) → compare_images / check_structure_sim
# ---------------------------------------------------------------------------
GIMP_TEMPLATE = {
    "domain": "gimp",
    "snapshot": "gimp",
    "related_apps": ["gimp"],
    "description": "Image editing in GIMP: crop, resize, color adjustments, layers, export.",
    "task_categories": [
        {
            "name": "basic_editing",
            "description": "Crop, resize, rotate, flip images",
            "verifier_strategy": "vm_file (image) → compare_images",
            "examples": [],
        },
        {
            "name": "color_adjustment",
            "description": "Brightness, contrast, saturation, color balance",
            "verifier_strategy": "vm_file (image) → check_structure_sim with color checks",
            "examples": [],
        },
        {
            "name": "export",
            "description": "Export in different formats (PNG, JPEG, BMP, etc.)",
            "verifier_strategy": "vm_command_line (file exists + format check) → check_include_exclude",
            "examples": [],
        },
    ],
}

# ---------------------------------------------------------------------------
# Domain: thunderbird
# Verifier pattern: vm_file (prefs.js) → check_thunderbird_prefs
# ---------------------------------------------------------------------------
THUNDERBIRD_TEMPLATE = {
    "domain": "thunderbird",
    "snapshot": "thunderbird",
    "related_apps": ["thunderbird"],
    "description": "Thunderbird email client: settings, filters, compose, account config.",
    "task_categories": [
        {
            "name": "settings",
            "description": "Change Thunderbird preferences and account settings",
            "verifier_strategy": "vm_file (prefs.js) → check_thunderbird_prefs",
            "examples": [],
        },
        {
            "name": "filters",
            "description": "Create and manage message filters",
            "verifier_strategy": "vm_file (msgFilterRules.dat) → check_thunderbird_filter",
            "examples": [],
        },
    ],
}

# ---------------------------------------------------------------------------
# Domain: vlc
# Verifier pattern: vm_command_line / vm_file → specialized checks
# ---------------------------------------------------------------------------
VLC_TEMPLATE = {
    "domain": "vlc",
    "snapshot": "vlc",
    "related_apps": ["vlc"],
    "description": "VLC media player: playback settings, preferences, interface customization.",
    "task_categories": [
        {
            "name": "settings",
            "description": "Change VLC preferences (playback, interface, audio, video)",
            "verifier_strategy": "vm_file (vlcrc) → check_include_exclude or specialized",
            "examples": [],
        },
    ],
}

# ---------------------------------------------------------------------------
# Aggregate all templates
# ---------------------------------------------------------------------------
ALL_TEMPLATES = {
    "os": OS_TEMPLATE,
    "libreoffice_calc": CALC_TEMPLATE,
    "libreoffice_writer": WRITER_TEMPLATE,
    "libreoffice_impress": IMPRESS_TEMPLATE,
    "chrome": CHROME_TEMPLATE,
    "vs_code": VSCODE_TEMPLATE,
    "gimp": GIMP_TEMPLATE,
    "thunderbird": THUNDERBIRD_TEMPLATE,
    "vlc": VLC_TEMPLATE,
}

# ---------------------------------------------------------------------------
# Verifier patterns that the LLM can use (deterministic, no LLM-as-Judge)
# Ordered by reliability: prefer top patterns
# ---------------------------------------------------------------------------
VERIFIER_PATTERNS = """
## Available Verifier Patterns (use ONLY these)

### Pattern 1: Command Output Check (most reliable)
Use when the task result can be verified by running a shell command.
```json
{
  "func": "check_include_exclude",
  "result": {
    "type": "vm_command_line",
    "command": ["bash", "-c", "<shell command that outputs result>"]
  },
  "expected": {
    "type": "rule",
    "rules": {
      "include": ["<string that must appear in output>"],
      "exclude": ["<string that must NOT appear>"]
    }
  }
}
```

### Pattern 2: Exact Match
Use when the command output must exactly equal an expected value.
```json
{
  "func": "exact_match",
  "result": {
    "type": "vm_command_line",
    "command": ["bash", "-c", "<shell command>"]
  },
  "expected": {
    "type": "rule",
    "rules": {
      "expected": "<exact expected output string>"
    }
  }
}
```

### Pattern 3: File Content Check
Use when you need to verify a text file's content.
```json
{
  "func": "check_include_exclude",
  "result": {
    "type": "vm_command_line",
    "command": ["bash", "-c", "cat /path/to/file"]
  },
  "expected": {
    "type": "rule",
    "rules": {
      "include": ["expected content"],
      "exclude": []
    }
  }
}
```

### Pattern 4: JSON Settings Check
Use when verifying application settings stored in JSON files.
```json
{
  "func": "check_json",
  "result": {
    "type": "vm_file",
    "path": "/path/to/settings.json",
    "dest": "settings.json"
  },
  "expected": {
    "type": "rule",
    "rules": {
      "expect": [
        {"key": ["path", "to", "setting"], "method": "eq", "ref": "expected_value"}
      ]
    }
  }
}
```

### Pattern 5: gsettings / dconf Check (GNOME settings)
Use when verifying GNOME desktop settings.
```json
{
  "func": "exact_match",
  "result": {
    "type": "vm_command_line",
    "command": ["gsettings", "get", "org.gnome.desktop.interface", "setting-key"]
  },
  "expected": {
    "type": "rule",
    "rules": {
      "expected": "'expected-value'"
    }
  }
}
```
"""
