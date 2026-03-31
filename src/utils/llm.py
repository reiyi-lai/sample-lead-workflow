# Claude API wrapper with web search support

import os
import json
import re
import time
import anthropic
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 65  # Wait after rate limit error before retrying


def get_client() -> anthropic.Anthropic:
    """Get Anthropic client with API key from environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return anthropic.Anthropic(api_key=api_key)


def call_claude(
    system_prompt: str,
    model: str,
    user_message: Optional[str] = None,
    messages: Optional[list] = None,
    max_tokens: int = 4096,
    enable_web_search: bool = False,
) -> str:
    """
    Call Claude API with optional web search and multi-turn support. 
    Provide either user_message (single turn) or messages (multi-turn).
    """
    if messages is None:
        messages = [{"role": "user", "content": user_message or "Go."}]

    client = get_client()

    request_kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": messages,
    }

    if enable_web_search:
        request_kwargs["tools"] = [
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 10,
            }
        ]

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(**request_kwargs)

            result_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    result_text += block.text

            return result_text

        except anthropic.RateLimitError as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_DELAY_SECONDS * (attempt + 1)
                print(f"\n  [Rate Limit] Waiting {wait_time}s before retry {attempt + 2}/{MAX_RETRIES}...")
                time.sleep(wait_time)
            else:
                raise

    raise last_error


def extract_json_from_response(response: str) -> dict:
    """
    Extract JSON from a Claude response that may contain other text.
    Uses multiple strategies: direct parse, markdown blocks, balanced braces.
    """
    import re
    import json

    text = response.strip()

    # Strategy 1: Try parsing the whole response directly
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from markdown code blocks (```json or ```)
    for pattern in [r"```json\s*([\s\S]*?)\s*```", r"```\s*([\s\S]*?)\s*```"]:
        for match in re.findall(pattern, text):
            if match.strip().startswith(("{", "[")):
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    pass

    # Strategy 3: Find JSON by balanced braces (handles text before/after JSON)
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start_idx = text.find(start_char)
        if start_idx == -1:
            continue

        depth = 0
        in_string = False
        escape_next = False

        for i in range(start_idx, len(text)):
            char = text[i]
            if escape_next:
                escape_next = False
                continue
            if char == "\\":
                escape_next = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == start_char:
                depth += 1
            elif char == end_char:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start_idx : i + 1])
                    except json.JSONDecodeError:
                        break

    # Strategy 4: First/last brace with trailing comma fix
    first_brace = text.find("{") if text.find("{") != -1 else text.find("[")
    last_brace = max(text.rfind("}"), text.rfind("]"))
    last_error = None

    if first_brace != -1 and last_brace != -1:
        candidate = text[first_brace : last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as e:
            last_error = f"Strategy 4a: {e}"
            fixed = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                return json.loads(fixed)
            except json.JSONDecodeError as e:
                last_error = f"Strategy 4b: {e}"

    # Strategy 5: Try to repair truncated JSON by finding last complete object
    if first_brace != -1:
        partial = text[first_brace:]

        # Try to find last complete "}" that's followed by "," or is part of array
        last_complete_idx = -1
        for i in range(len(partial) - 1, -1, -1):
            if partial[i] == '}':
                rest = partial[i+1:].lstrip()
                if rest.startswith(',') or rest.startswith(']'):
                    last_complete_idx = i
                    break

        if last_complete_idx > 0:
            truncated = partial[:last_complete_idx + 1]
            open_braces = truncated.count('{') - truncated.count('}')
            open_brackets = truncated.count('[') - truncated.count(']')
            truncated += ']' * open_brackets + '}' * open_braces
            try:
                return json.loads(truncated)
            except json.JSONDecodeError as e:
                last_error = f"Strategy 5a: {e}"

        # Fallback: simple brace counting and closing
        open_braces = 0
        open_brackets = 0
        in_string = False
        escape_next = False

        for char in partial:
            if escape_next:
                escape_next = False
                continue
            if char == "\\":
                escape_next = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == "{":
                open_braces += 1
            elif char == "}":
                open_braces -= 1
            elif char == "[":
                open_brackets += 1
            elif char == "]":
                open_brackets -= 1

        if open_braces > 0 or open_brackets > 0:
            repaired = partial.rstrip()
            if repaired.endswith(","):
                repaired = repaired[:-1]
            repaired += "]" * open_brackets + "}" * open_braces
            try:
                return json.loads(repaired)
            except json.JSONDecodeError as e:
                last_error = f"Strategy 5b: {e}"

    # Strategy 6: Try to fix common JSON issues
    if first_brace != -1:
        partial = text[first_brace:]

        # Try multiple fixes
        fixes = [
            # Fix 1: Remove trailing commas before } or ]
            lambda s: re.sub(r',(\s*[}\]])', r'\1', s),

            # Fix 2: Fix unescaped quotes in strings
            lambda s: re.sub(r'(?<!\\)"(?=[^"]*"[^"]*:)', '\\"', s),

            # Fix 3: Clean up malformed JSON structure
            lambda s: re.sub(r',\s*}', '}', re.sub(r',\s*]', ']', s)),

            # Fix 4: Remove any control characters or invalid JSON characters
            lambda s: re.sub(r'[\x00-\x1f\x7f-\x9f]', '', s)
        ]

        for i, fix_func in enumerate(fixes):
            try:
                fixed = fix_func(partial)
                result = json.loads(fixed)
                return result
            except (json.JSONDecodeError, re.error) as e:
                last_error = f"Strategy 6.{i+1}: {e}"
                continue

    error_msg = f"Failed to parse JSON - {last_error}" if last_error else "Failed to parse JSON"
    return {"error": error_msg, "raw_response": response[:2000]}
