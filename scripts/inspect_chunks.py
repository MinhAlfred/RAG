"""Inspect processed chunks - Xem thông tin chunks đã tạo"""

import sys
import json
import argparse
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings


def inspect_chunks_file(json_path: Path):
    """Inspect a single chunks JSON file"""

    with open(json_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"\n{'=' * 70}")
    print(f"📄 File: {json_path.name}")
    print(f"{'=' * 70}\n")

    # Basic stats
    print(f"📊 Basic Statistics:")
    print(f"   Total chunks: {len(chunks):,}")

    if not chunks:
        return

    # Subject info
    subjects = Counter(c['metadata'].get('subject') for c in chunks)
    subject_keys = Counter(c['metadata'].get('subject_key') for c in chunks)

    print(f"   Subject: {list(subjects.keys())[0] if subjects else 'N/A'}")

    # Grade info
    grades = Counter(c['metadata'].get('grade') for c in chunks if c['metadata'].get('grade'))
    if grades:
        print(f"   Grades: {', '.join(map(str, sorted(grades.keys())))}")

    # Token stats
    total_tokens = sum(c.get('token_count', 0) for c in chunks)
    avg_tokens = total_tokens // len(chunks) if chunks else 0
    print(f"   Total tokens: {total_tokens:,}")
    print(f"   Avg tokens/chunk: {avg_tokens}")

    # Page coverage
    pages = set(c['metadata'].get('page_number') for c in chunks if c['metadata'].get('page_number'))
    print(f"   Pages: {len(pages)}")

    # Chapter info
    chapters = Counter(c['metadata'].get('chapter') for c in chunks if c['metadata'].get('chapter'))
    if chapters:
        print(f"   Chapters: {', '.join(map(str, sorted(chapters.keys())))}")

    # Content features
    has_code = sum(1 for c in chunks if c['metadata'].get('has_code'))
    has_formula = sum(1 for c in chunks if c['metadata'].get('has_formula'))
    has_table = sum(1 for c in chunks if c['metadata'].get('has_table'))

    print(f"\n📝 Content Features:")
    print(f"   Has code: {has_code} chunks ({has_code / len(chunks) * 100:.1f}%)")
    print(f"   Has formula: {has_formula} chunks ({has_formula / len(chunks) * 100:.1f}%)")
    print(f"   Has table: {has_table} chunks ({has_table / len(chunks) * 100:.1f}%)")

    # Topics
    all_topics = []
    for c in chunks:
        all_topics.extend(c['metadata'].get('topics', []))

    topic_counts = Counter(all_topics)

    if topic_counts:
        print(f"\n🏷️  Top Topics:")
        for topic, count in topic_counts.most_common(10):
            print(f"   {topic}: {count}")

    # Sample chunks
    print(f"\n📝 Sample Chunks (first 3):")
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"\n   --- Chunk {i} ---")
        print(f"   ID: {chunk['chunk_id']}")
        print(f"   Page: {chunk['metadata'].get('page_number')}")
        print(f"   Chapter: {chunk['metadata'].get('chapter_title', 'N/A')}")
        print(f"   Topics: {', '.join(chunk['metadata'].get('topics', [])[:3])}")
        print(f"   Content: {chunk['content'][:150]}...")


def inspect_directory(dir_path: Path):
    """Inspect all chunk files in directory"""

    # Find all JSON files
    json_files = list(dir_path.rglob("*_chunks.json"))

    if not json_files:
        print(f"❌ No chunk files found in {dir_path}")
        return

    print(f"\n{'=' * 70}")
    print(f"📁 Directory: {dir_path}")
    print(f"{'=' * 70}")
    print(f"\nFound {len(json_files)} chunk files\n")

    # Summary stats
    total_chunks = 0
    total_tokens = 0
    subjects_found = set()
    grades_found = set()

    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)

        total_chunks += len(chunks)
        total_tokens += sum(c.get('token_count', 0) for c in chunks)

        for chunk in chunks:
            if chunk['metadata'].get('subject'):
                subjects_found.add(chunk['metadata']['subject'])
            if chunk['metadata'].get('grade'):
                grades_found.add(chunk['metadata']['grade'])

        print(f"   {json_file.name:50s} {len(chunks):>6,} chunks")

    print(f"\n{'=' * 70}")
    print(f"📊 Summary:")
    print(f"   Total files: {len(json_files)}")
    print(f"   Total chunks: {total_chunks:,}")
    print(f"   Total tokens: {total_tokens:,}")
    print(f"   Subjects: {', '.join(sorted(subjects_found))}")
    print(f"   Grades: {', '.join(map(str, sorted(grades_found)))}")
    print(f"{'=' * 70}")


def main():
    parser = argparse.ArgumentParser(
        description="Inspect processed chunk files"
    )
    parser.add_argument(
        "path",
        type=str,
        help="Path to chunks JSON file or directory"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed info for each file in directory"
    )

    args = parser.parse_args()

    path = Path(args.path)

    if not path.exists():
        print(f"❌ Path not found: {path}")
        return

    if path.is_file():
        inspect_chunks_file(path)
    elif path.is_dir():
        if args.detailed:
            # Show detailed info for each file
            json_files = list(path.rglob("*_chunks.json"))
            for json_file in json_files:
                inspect_chunks_file(json_file)
        else:
            # Show summary only
            inspect_directory(path)
    else:
        print(f"❌ Invalid path: {path}")


if __name__ == "__main__":
    main()

