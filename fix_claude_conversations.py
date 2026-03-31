#!/usr/bin/env python3
"""
Claude Code Conversation Repair Tool
=====================================
Fixes the "Cannot read properties of undefined (reading 'trim')" error
that occurs when resuming sessions with `claude --resume`.

Known bug: https://github.com/anthropics/claude-code/issues/16721

Usage:
    # Scan all conversations for issues
    python3 fix_claude_conversations.py --scan

    # Repair all broken conversations
    python3 fix_claude_conversations.py --repair

    # Repair a specific conversation file
    python3 fix_claude_conversations.py --repair --file <path_to_jsonl>

    # Export a conversation to readable markdown
    python3 fix_claude_conversations.py --export --file <path_to_jsonl>
"""

import json
import os
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime


CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"


def get_all_jsonl_files():
    """Find all conversation JSONL files."""
    if not PROJECTS_DIR.exists():
        print(f"Error: {PROJECTS_DIR} does not exist.")
        return []
    files = list(PROJECTS_DIR.rglob("*.jsonl"))
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)


def diagnose_file(filepath):
    """Check a JSONL file for common issues that cause the trim error."""
    issues = []
    lines = []

    try:
        with open(filepath, "r") as f:
            raw_lines = f.readlines()
    except Exception as e:
        return [f"Cannot read file: {e}"], []

    for i, raw_line in enumerate(raw_lines):
        stripped = raw_line.strip()
        if not stripped:
            issues.append(f"  Line {i}: Empty line")
            continue

        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as e:
            issues.append(f"  Line {i}: Invalid JSON - {e}")
            lines.append(None)
            continue

        lines.append(data)

        # Check for message entries with missing/null content
        msg = data.get("message", {})
        if isinstance(msg, dict):
            role = msg.get("role", "")
            content = msg.get("content")

            # Case 1: content is None/null
            if content is None and role in ("user", "assistant"):
                issues.append(f"  Line {i}: {role} message has null content")

            # Case 2: content is a list with problematic blocks
            elif isinstance(content, list):
                for j, block in enumerate(content):
                    if not isinstance(block, dict):
                        issues.append(f"  Line {i}: content block {j} is not a dict: {type(block)}")
                        continue
                    block_type = block.get("type", "")
                    if block_type == "text" and block.get("text") is None:
                        issues.append(f"  Line {i}: text block {j} has null 'text' field")
                    if block_type == "thinking" and block.get("thinking") is None:
                        issues.append(f"  Line {i}: thinking block {j} has null 'thinking' field")
                    if block_type == "tool_use":
                        if block.get("name") is None:
                            issues.append(f"  Line {i}: tool_use block {j} has null 'name'")
                    if block_type == "tool_result":
                        tool_content = block.get("content")
                        if tool_content is None:
                            issues.append(f"  Line {i}: tool_result block {j} has null content")
                        elif isinstance(tool_content, list):
                            for k, tc in enumerate(tool_content):
                                if isinstance(tc, dict) and tc.get("type") == "text" and tc.get("text") is None:
                                    issues.append(f"  Line {i}: tool_result block {j} sub-block {k} has null text")

            # Case 3: content is a string (should be fine, but check for undefined-like values)
            elif isinstance(content, str):
                if content.strip() == "undefined":
                    issues.append(f"  Line {i}: {role} message content is literally 'undefined'")

        # Check for missing 'type' field
        if "type" not in data and "message" not in data:
            issues.append(f"  Line {i}: Entry has no 'type' or 'message' field")

        # Check summary field (used by resume picker)
        summary = data.get("summary")
        if summary is not None and not isinstance(summary, str):
            issues.append(f"  Line {i}: 'summary' field is not a string: {type(summary)}")

    return issues, lines


def repair_file(filepath, dry_run=False):
    """Repair a JSONL file by fixing common issues."""
    issues, _ = diagnose_file(filepath)
    if not issues:
        return False, "No issues found"

    # Create backup
    backup_path = str(filepath) + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if not dry_run:
        shutil.copy2(filepath, backup_path)

    fixed_lines = []
    fixes_applied = 0

    with open(filepath, "r") as f:
        raw_lines = f.readlines()

    for i, raw_line in enumerate(raw_lines):
        stripped = raw_line.strip()
        if not stripped:
            fixes_applied += 1
            continue  # Skip empty lines

        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            fixes_applied += 1
            continue  # Skip corrupted lines

        modified = False

        msg = data.get("message", {})
        if isinstance(msg, dict):
            role = msg.get("role", "")
            content = msg.get("content")

            # Fix null content
            if content is None and role == "user":
                data["message"]["content"] = ""
                modified = True
                fixes_applied += 1
            elif content is None and role == "assistant":
                data["message"]["content"] = [{"type": "text", "text": ""}]
                modified = True
                fixes_applied += 1

            # Fix content list blocks
            elif isinstance(content, list):
                new_content = []
                for block in content:
                    if not isinstance(block, dict):
                        fixes_applied += 1
                        continue
                    block_type = block.get("type", "")

                    if block_type == "text" and block.get("text") is None:
                        block["text"] = ""
                        modified = True
                        fixes_applied += 1
                    if block_type == "thinking" and block.get("thinking") is None:
                        block["thinking"] = ""
                        modified = True
                        fixes_applied += 1
                    if block_type == "tool_use" and block.get("name") is None:
                        block["name"] = "unknown_tool"
                        modified = True
                        fixes_applied += 1
                    if block_type == "tool_result":
                        tool_content = block.get("content")
                        if tool_content is None:
                            block["content"] = ""
                            modified = True
                            fixes_applied += 1
                        elif isinstance(tool_content, list):
                            for tc in tool_content:
                                if isinstance(tc, dict) and tc.get("type") == "text" and tc.get("text") is None:
                                    tc["text"] = ""
                                    modified = True
                                    fixes_applied += 1

                    new_content.append(block)

                if modified:
                    data["message"]["content"] = new_content

            elif isinstance(content, str) and content.strip() == "undefined":
                data["message"]["content"] = ""
                modified = True
                fixes_applied += 1

        # Fix summary field
        summary = data.get("summary")
        if summary is not None and not isinstance(summary, str):
            data["summary"] = str(summary) if summary else ""
            modified = True
            fixes_applied += 1

        fixed_lines.append(json.dumps(data))

    if not dry_run and fixes_applied > 0:
        with open(filepath, "w") as f:
            f.write("\n".join(fixed_lines) + "\n")

    return fixes_applied > 0, f"Applied {fixes_applied} fixes (backup: {backup_path})" if not dry_run else f"Would apply {fixes_applied} fixes"


def export_conversation(filepath, output_path=None):
    """Export a conversation to readable markdown."""
    if output_path is None:
        output_path = str(filepath).replace(".jsonl", "_export.md")

    lines = []
    with open(filepath, "r") as f:
        for raw_line in f:
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError:
                continue

            msg = data.get("message", {})
            if not isinstance(msg, dict):
                continue

            role = msg.get("role", "")
            content = msg.get("content", "")
            timestamp = data.get("timestamp", "")

            if role not in ("user", "assistant"):
                continue

            text_parts = []
            if isinstance(content, str):
                text_parts.append(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "unknown")
                            tool_input = json.dumps(block.get("input", {}), indent=2)
                            text_parts.append(f"[Tool: {tool_name}]\n```json\n{tool_input}\n```")
                        elif block.get("type") == "tool_result":
                            result_content = block.get("content", "")
                            if isinstance(result_content, list):
                                for rc in result_content:
                                    if isinstance(rc, dict) and rc.get("type") == "text":
                                        text_parts.append(f"[Tool Result]\n{rc.get('text', '')}")
                            elif isinstance(result_content, str):
                                text_parts.append(f"[Tool Result]\n{result_content}")

            if not text_parts or all(not t for t in text_parts):
                continue

            header = f"## {'🧑 User' if role == 'user' else '🤖 Assistant'}"
            if timestamp:
                header += f" ({timestamp})"

            lines.append(header)
            lines.append("")
            lines.append("\n".join(text_parts))
            lines.append("")
            lines.append("---")
            lines.append("")

    output = "\n".join(lines)
    with open(output_path, "w") as f:
        f.write(output)

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Claude Code Conversation Repair Tool")
    parser.add_argument("--scan", action="store_true", help="Scan all conversations for issues")
    parser.add_argument("--repair", action="store_true", help="Repair broken conversations")
    parser.add_argument("--export", action="store_true", help="Export conversation to markdown")
    parser.add_argument("--file", type=str, help="Specific JSONL file to operate on")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without changing files")
    parser.add_argument("--all", action="store_true", help="Process all conversation files")

    args = parser.parse_args()

    if not any([args.scan, args.repair, args.export]):
        parser.print_help()
        return

    if args.file:
        files = [Path(args.file)]
    elif args.all or args.scan:
        files = get_all_jsonl_files()
    else:
        files = get_all_jsonl_files()

    if not files:
        print("No conversation files found.")
        return

    if args.scan:
        print(f"Scanning {len(files)} conversation file(s)...\n")
        broken_count = 0
        for f in files:
            issues, _ = diagnose_file(f)
            if issues:
                broken_count += 1
                print(f"❌ {f.name} ({f.parent.name})")
                for issue in issues:
                    print(f"   {issue}")
                print()
            else:
                print(f"✅ {f.name} ({f.parent.name})")
        print(f"\nSummary: {broken_count}/{len(files)} files have issues")

    elif args.repair:
        if args.file:
            files_to_repair = [Path(args.file)]
        else:
            # Only repair files with issues
            files_to_repair = []
            for f in files:
                issues, _ = diagnose_file(f)
                if issues:
                    files_to_repair.append(f)

        if not files_to_repair:
            print("No files need repair!")
            return

        print(f"Repairing {len(files_to_repair)} file(s)...\n")
        for f in files_to_repair:
            fixed, msg = repair_file(f, dry_run=args.dry_run)
            status = "🔧" if fixed else "⏭️"
            print(f"{status} {f.name}: {msg}")

    elif args.export:
        if not args.file:
            print("Error: --export requires --file <path>")
            return
        output = export_conversation(Path(args.file))
        print(f"Exported to: {output}")


if __name__ == "__main__":
    main()