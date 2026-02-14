#!/usr/bin/env -S uv run --project backend python
import sys
from pathlib import Path

# Add backend to sys.path to import app.config
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.config import Settings


def generate_env_table() -> str:
    """Generate Markdown table for environment variables."""
    lines = [
        "| Environment Variable | Default Value | Description |",
        "| -------------------- | ------------- | ----------- |",
    ]

    # Get fields from Settings
    # Try to get field descriptions from the class docstring or comments if possible,
    # but Pydantic's model_fields is easier for types and defaults.
    fields = Settings.model_fields

    for name, field in fields.items():
        env_name = name.upper()
        # Default value
        default = field.default
        if default is None:
            default = "*None*"
        elif isinstance(default, str):
            default = f"`{default}`"
        else:
            default = f"`{default}`"

        description = field.description or ""

        lines.append(f"| `{env_name}` | {default} | {description} |")

    return "\n".join(lines)


def update_readme(readme_path: Path, table: str, check: bool = False) -> bool:
    """Update README.md with the generated table."""
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = "<!-- ENV_VARS_START -->"
    end_marker = "<!-- ENV_VARS_END -->"

    if start_marker not in content or end_marker not in content:
        print(
            f"Error: Markers {start_marker} and {end_marker} not found in {readme_path}"
        )
        return False

    new_content = (
        content.split(start_marker)[0]
        + start_marker
        + "\n\n"
        + table
        + "\n\n"
        + end_marker
        + content.split(end_marker)[1]
    )

    if content == new_content:
        print("README.md is already up to date.")
        return True

    if check:
        print(
            "Error: README.md is out of date. Run scripts/sync_env_docs.py to update."
        )
        return False

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("Updated README.md with latest environment variable configuration.")
    return True


if __name__ == "__main__":
    check_mode = "--check" in sys.argv
    root_dir = Path(__file__).parent.parent
    readme_file = root_dir / "README.md"

    env_table = generate_env_table()

    if not update_readme(readme_file, env_table, check_mode):
        sys.exit(1)
