# utils/llm.py
# Claude API wrapper with web search support

import os
import json
import time
import anthropic
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Rate limit handling
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 65  # Wait just over 1 minute for rate limit to reset


def get_client() -> anthropic.Anthropic:
    """Get Anthropic client with API key from environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return anthropic.Anthropic(api_key=api_key)


def call_claude(
    system_prompt: str,
    user_message: str,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
    enable_web_search: bool = False,
) -> str:
    """
    Call Claude API with optional web search capability.

    Args:
        system_prompt: System prompt for Claude
        user_message: User message/query
        model: Model to use (default: claude-sonnet-4-20250514)
        max_tokens: Maximum tokens in response
        enable_web_search: Whether to enable web search tool

    Returns:
        Claude's response text
    """
    client = get_client()

    messages = [{"role": "user", "content": user_message}]

    # Build request kwargs
    request_kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": messages,
    }

    # Add web search tool if enabled
    if enable_web_search:
        request_kwargs["tools"] = [
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 10,
            }
        ]

    # Retry logic for rate limits
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(**request_kwargs)

            # Extract text from response
            result_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    result_text += block.text

            return result_text

        except anthropic.RateLimitError as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_DELAY_SECONDS * (attempt + 1)
                print(f"\n⚠️  Rate limit hit. Waiting {wait_time}s before retry {attempt + 2}/{MAX_RETRIES}...")
                time.sleep(wait_time)
            else:
                raise

    raise last_error


def call_claude_with_web_search(
    system_prompt: str,
    user_message: str,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 8192,
) -> str:
    """
    Call Claude with web search enabled.
    Convenience wrapper for discovery tasks.
    """
    return call_claude(
        system_prompt=system_prompt,
        user_message=user_message,
        model=model,
        max_tokens=max_tokens,
        enable_web_search=True,
    )


def call_claude_conversation(
    system_prompt: str,
    messages: list,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
    enable_web_search: bool = False,
) -> str:
    """
    Call Claude API with multi-turn conversation support.

    Args:
        system_prompt: System prompt for Claude
        messages: List of message dicts with 'role' and 'content' keys
                  e.g., [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        model: Model to use
        max_tokens: Maximum tokens in response
        enable_web_search: Whether to enable web search tool

    Returns:
        Claude's response text
    """
    client = get_client()

    # Build request kwargs
    request_kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": messages,
    }

    # Add web search tool if enabled
    if enable_web_search:
        request_kwargs["tools"] = [
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 10,
            }
        ]

    # Retry logic for rate limits
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(**request_kwargs)

            # Extract text from response
            result_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    result_text += block.text

            return result_text

        except anthropic.RateLimitError as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_DELAY_SECONDS * (attempt + 1)
                print(f"\n⚠️  Rate limit hit. Waiting {wait_time}s before retry {attempt + 2}/{MAX_RETRIES}...")
                time.sleep(wait_time)
            else:
                raise

    raise last_error


def call_claude_json(
    system_prompt: str,
    user_message: str,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
) -> dict:
    """
    Call Claude and parse response as JSON.

    Returns:
        Parsed JSON response as dict
    """
    response = call_claude(
        system_prompt=system_prompt,
        user_message=user_message,
        model=model,
        max_tokens=max_tokens,
        enable_web_search=False,
    )

    # Try to extract JSON from response
    # Handle cases where Claude wraps JSON in markdown code blocks
    text = response.strip()

    # Remove markdown code blocks if present
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Return raw text in error case for debugging
        return {
            "error": "Failed to parse JSON",
            "parse_error": str(e),
            "raw_response": response,
        }


def extract_json_from_response(response: str) -> dict:
    """
    Extract JSON from a Claude response that may contain other text.
    Uses multiple strategies: direct parse, markdown blocks, balanced braces.
    """
    import re

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

        # Find the last complete object by looking for "}," or "}\n" pattern
        # This handles truncated arrays of objects (like company lists)
        last_complete_patterns = [
            r'\},\s*\{[^}]*$',  # Truncated in middle of next object
            r'\},\s*$',         # Ends right after a complete object
            r'\}\s*\][^]]*$',   # Truncated after array closes
        ]

        # Try to find last complete "}" that's followed by "," or is part of array
        # Look for the last "}," and truncate after it
        last_complete_idx = -1
        for i in range(len(partial) - 1, -1, -1):
            if partial[i] == '}':
                # Check if this is followed by comma (part of array)
                rest = partial[i+1:].lstrip()
                if rest.startswith(',') or rest.startswith(']'):
                    last_complete_idx = i
                    break

        if last_complete_idx > 0:
            # Truncate to last complete object
            truncated = partial[:last_complete_idx + 1]
            # Count remaining open brackets
            open_braces = truncated.count('{') - truncated.count('}')
            open_brackets = truncated.count('[') - truncated.count(']')
            # Close them
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

    error_msg = f"Failed to parse JSON - {last_error}" if last_error else "Failed to parse JSON"
    return {"error": error_msg, "raw_response": response[:2000]}
