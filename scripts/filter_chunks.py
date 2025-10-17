"""Filter chunks by criteria"""

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sgk_rag.utils.file_utils import save_json


def filter_chunks(
    input_file: Path,
    output_file: Path,
    subject: str = None,
    grade: int = None,
    has_code: bool = None,
    has_formula: bool = None,
    min_tokens: int = None,
    max_tokens: int = None
):
    """Filter chunks by criteria"""

    with open(input_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"\n{'='*70}")
    print(f"🔍 Filtering Chunks")
    print(f"{'='*70}")
    print(f"   Input: {input_file.name}")
    print(f"   Total chunks: {len(chunks):,}\n")

    # Apply filters
    filtered = chunks

    if subject:
        filtered = [c for c in filtered if c['metadata'].get('subject_key') == subject]
        print(f"   ✓ Filter by subject '{subject}': {len(filtered):,} chunks")

    if grade:
        filtered = [c for c in filtered if c['metadata'].get('grade') == grade]
        print(f"   ✓ Filter by grade {grade}: {len(filtered):,} chunks")

    if has_code is not None:
        filtered = [c for c in filtered if c['metadata'].get('has_code') == has_code]
        print(f"   ✓ Filter by has_code={has_code}: {len(filtered):,} chunks")

    if has_formula is not None:
        filtered = [c for c in filtered if c['metadata'].get('has_formula') == has_formula]
        print(f"   ✓ Filter by has_formula={has_formula}: {len(filtered):,} chunks")

    if min_tokens:
        filtered = [c for c in filtered if c.get('token_count', 0) >= min_tokens]
        print(f"   ✓ Filter by min_tokens>={min_tokens}: {len(filtered):,} chunks")

    if max_tokens:
        filtered = [c for c in filtered if c.get('token_count', 0) <= max_tokens]
        print(f"   ✓ Filter by max_tokens<={max_tokens}: {len(filtered):,} chunks")

    # Save filtered chunks
    save_json(filtered, output_file)

    print(f"\n{'='*70}")
    print(f"✅ Filtering Complete!")
    print(f"{'='*70}")
    print(f"   Filtered chunks: {len(filtered):,}")
    print(f"   Reduction: {(1 - len(filtered)/len(chunks))*100:.1f}%")
    print(f"   Output: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Filter chunks by various criteria"
    )
    parser.add_argument(
        "input",
        type=str,
        help="Input chunks JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output filtered file"
    )
    parser.add_argument(
        "--subject",
        type=str,
        help="Filter by subject key (tin_hoc, toan, etc.)"
    )
    parser.add_argument(
        "--grade",
        type=int,
        help="Filter by grade (3-12)"
    )
    parser.add_argument(
        "--has-code",
        action="store_true",
        help="Only chunks with code"
    )
    parser.add_argument(
        "--has-formula",
        action="store_true",
        help="Only chunks with formulas"
    )
    parser.add_argument(
        "--min-tokens",
        type=int,
        help="Minimum token count"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        help="Maximum token count"
    )

    args = parser.parse_args()

    input_file = Path(args.input)
    output_file = Path(args.output)

    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        return

    filter_chunks(
        input_file,
        output_file,
        subject=args.subject,
        grade=args.grade,
        has_code=args.has_code if args.has_code else None,
        has_formula=args.has_formula if args.has_formula else None,
        min_tokens=args.min_tokens,
        max_tokens=args.max_tokens
    )


if __name__ == "__main__":
    main()