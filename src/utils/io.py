# Shared file I/O helpers used across all stages

import os
import json
from typing import Optional

from constants import sanitize_name


def load_json(path: str) -> Optional[dict]:
    """Load JSON file if it exists, else return None."""
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def save_json(path: str, data):
    """Save data to JSON file, creating parent dirs as needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def company_path(base_dir: str, company_name: str, filename: str) -> str:
    """Path to a file in a company's folder: base_dir/SanitizedName/filename."""
    return os.path.join(base_dir, sanitize_name(company_name), filename)
