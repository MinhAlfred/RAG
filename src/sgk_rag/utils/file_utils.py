import json
from pathlib import Path
from typing import List, Any


def save_json(data: Any, output_path: Path, indent: int = 2, ensure_ascii: bool = False):
    """
    Save Python object (list, dict, etc.) to a JSON file safely.

    Args:
        data: Python object to save (usually list[dict] for chunks)
        output_path (Path): Path to output JSON file
        indent (int): Indentation for readability
        ensure_ascii (bool): Whether to escape non-ASCII characters (default False)
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        print(f"💾 Saved JSON: {output_path} ({len(data):,} items)")
    except Exception as e:
        print(f"❌ Failed to save JSON file: {e}")
        raise


def load_json(json_path: Path) -> Any:
    """
    Load JSON file safely and return its content.

    Args:
        json_path (Path): Path to JSON file
    Returns:
        Any: Python object (dict or list)
    """
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {json_path}: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to read JSON file {json_path}: {e}")


def get_pdf_files(directory: Path) -> List[Path]:
    """
    Return a list of all PDF files in a directory (non-recursive).

    Args:
        directory (Path): Directory to search
    Returns:
        List[Path]: List of PDF file paths
    """
    if not directory.exists():
        print(f"⚠️  Directory not found: {directory}")
        return []

    pdf_files = sorted(directory.glob("*.pdf"))
    return pdf_files


def list_files_recursive(directory: Path, pattern: str = "*") -> List[Path]:
    """
    Recursively list all files in directory matching a pattern.

    Args:
        directory (Path): Root directory
        pattern (str): Filename pattern, e.g. '*.json', '*.pdf'
    Returns:
        List[Path]: List of matching file paths
    """
    if not directory.exists():
        print(f"⚠️  Directory not found: {directory}")
        return []

    return sorted(directory.rglob(pattern))


def read_text_file(file_path: Path) -> str:
    """
    Read content of a text file safely.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Failed to read file {file_path}: {e}")


def save_text_file(content: str, output_path: Path):
    """
    Save text content to a file safely.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📝 Saved text file: {output_path}")
    except Exception as e:
        print(f"❌ Failed to save text file {output_path}: {e}")
        raise
