"""Merge multiple chunk files into one"""

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sgk_rag.utils.file_utils import save_json


def merge_chunk_files(input_files: list, output_file: Path):
    """Merge multiple chunk JSON files"""

    all_chunks = []

    print(f"\n{'='*70}")
    print(f"🔄 Merging {len(input_files)} files")
    print(f"{'='*70}\n")

    for input_file in input_files:
        with open(input_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)

        all_chunks.extend(chunks)
        print(f"   ✓ {input_file.name:50s} {len(chunks):>6,} chunks")

    # Save merged file
    save_json(all_chunks, output_file)

    print(f"\n{'='*70}")
    print(f"✅ Merged Successfully!")
    print(f"{'='*70}")
    print(f"   Total chunks: {len(all_chunks):,}")
    print(f"   Output: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Merge multiple chunk files into one"
    )
    parser.add_argument(
        "input",
        type=str,
        nargs='+',
        help="Input chunk JSON files"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output merged file"
    )

    args = parser.parse_args()

    input_files = [Path(f) for f in args.input]
    output_file = Path(args.output)

    # Validate input files
    for f in input_files:
        if not f.exists():
            print(f"❌ File not found: {f}")
            return

    merge_chunk_files(input_files, output_file)


if __name__ == "__main__":
    main()