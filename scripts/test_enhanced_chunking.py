"""
Test Enhanced Chunking vs Current Chunking
Compare quality and performance
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.sgk_rag.core.document_processor import DocumentProcessor
from src.sgk_rag.core.document_processor_enhanced import EnhancedDocumentProcessor


def compare_chunking():
    """Compare old vs enhanced chunking"""

    print("=" * 80)
    print("🔬 Comparing Chunking Methods")
    print("=" * 80)

    # Test file
    test_file = project_root / "data" / "raw" / "sgk_tin_hoc_10.txt"

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return

    print(f"\n📄 Test file: {test_file.name}\n")

    # Process with OLD method
    print("1️⃣  Processing with CURRENT method...")
    old_processor = DocumentProcessor(
        chunk_size=1000,  # characters
        chunk_overlap=200,
        smart_chunking=True  # Actually does nothing
    )

    old_chunks = old_processor.process_txt(test_file)

    print(f"   ✓ Created {len(old_chunks)} chunks")
    print(f"   - Avg tokens: {sum(c['token_count'] for c in old_chunks) / len(old_chunks):.0f}")
    print(f"   - Avg chars: {sum(len(c['content']) for c in old_chunks) / len(old_chunks):.0f}")

    # Process with ENHANCED method
    print("\n2️⃣  Processing with ENHANCED method...")
    new_processor = EnhancedDocumentProcessor(
        chunk_size=512,  # tokens!
        chunk_overlap=50,
        smart_chunking=True,
        add_context_windows=True
    )

    new_chunks = new_processor.process_txt(test_file)

    print(f"   ✓ Created {len(new_chunks)} chunks")
    print(f"   - Avg tokens: {sum(c['token_count'] for c in new_chunks) / len(new_chunks):.0f}")
    print(f"   - Avg chars: {sum(len(c['content']) for c in new_chunks) / len(new_chunks):.0f}")

    # Compare metrics
    print("\n" + "=" * 80)
    print("📊 Comparison Results")
    print("=" * 80)

    print(f"\n📈 Chunk Count:")
    print(f"   Old: {len(old_chunks)}")
    print(f"   New: {len(new_chunks)}")
    print(f"   Difference: {len(new_chunks) - len(old_chunks):+d} ({(len(new_chunks) / len(old_chunks) - 1) * 100:+.1f}%)")

    print(f"\n🎯 Token Distribution:")
    old_tokens = [c['token_count'] for c in old_chunks]
    new_tokens = [c['token_count'] for c in new_chunks]

    print(f"   Old: min={min(old_tokens)}, max={max(old_tokens)}, avg={sum(old_tokens) / len(old_tokens):.0f}")
    print(f"   New: min={min(new_tokens)}, max={max(new_tokens)}, avg={sum(new_tokens) / len(new_tokens):.0f}")

    print(f"\n🧩 Semantic Integrity:")
    old_complete = sum(1 for c in old_chunks if c.get('is_complete_section', False))
    new_complete = sum(1 for c in new_chunks if c.get('is_complete_section', False))

    print(f"   Old: {old_complete}/{len(old_chunks)} complete sections ({old_complete / len(old_chunks) * 100:.1f}%)")
    print(f"   New: {new_complete}/{len(new_chunks)} complete sections ({new_complete / len(new_chunks) * 100:.1f}%)")

    print(f"\n📝 Metadata Completeness:")

    def check_metadata_completeness(chunks):
        complete = 0
        for c in chunks:
            meta = c['metadata']
            if all([
                meta.get('chapter'),
                meta.get('lesson_number'),
                meta.get('grade'),
                meta.get('content_types')  # New field
            ]):
                complete += 1
        return complete

    old_meta = check_metadata_completeness(old_chunks)
    new_meta = check_metadata_completeness(new_chunks)

    print(f"   Old: {old_meta}/{len(old_chunks)} ({old_meta / len(old_chunks) * 100:.1f}%)")
    print(f"   New: {new_meta}/{len(new_chunks)} ({new_meta / len(new_chunks) * 100:.1f}%)")

    print(f"\n🏷️  Content Type Detection:")
    new_with_types = sum(1 for c in new_chunks if c['metadata'].get('content_types'))
    print(f"   Chunks with content types: {new_with_types}/{len(new_chunks)} ({new_with_types / len(new_chunks) * 100:.1f}%)")

    # Content type breakdown
    all_types = {}
    for c in new_chunks:
        for ctype in c['metadata'].get('content_types', []):
            all_types[ctype] = all_types.get(ctype, 0) + 1

    if all_types:
        print(f"\n   Content type distribution:")
        for ctype, count in sorted(all_types.items(), key=lambda x: -x[1]):
            print(f"      - {ctype}: {count} chunks")

    print(f"\n🎨 Context Windows:")
    new_with_context = sum(1 for c in new_chunks if c['metadata'].get('prev_chunk_preview') or c['metadata'].get('next_chunk_preview'))
    print(f"   Chunks with context: {new_with_context}/{len(new_chunks)} ({new_with_context / len(new_chunks) * 100:.1f}%)")

    # Sample comparison
    print("\n" + "=" * 80)
    print("📖 Sample Chunk Comparison")
    print("=" * 80)

    print("\n🔴 OLD METHOD - Sample Chunk #5:")
    print("-" * 80)
    old_sample = old_chunks[5]
    print(f"Tokens: {old_sample['token_count']}, Chars: {len(old_sample['content'])}")
    print(f"Complete section: {old_sample.get('is_complete_section', False)}")
    print(f"\nContent preview:")
    print(old_sample['content'][:400] + "...\n")

    print("\n🟢 NEW METHOD - Sample Chunk #5:")
    print("-" * 80)
    new_sample = new_chunks[5]
    print(f"Tokens: {new_sample['token_count']}, Chars: {len(new_sample['content'])}")
    print(f"Complete section: {new_sample.get('is_complete_section', False)}")
    print(f"Section type: {new_sample['metadata'].get('section_type', 'N/A')}")
    print(f"Content types: {new_sample['metadata'].get('content_types', [])}")
    print(f"Has context window: {bool(new_sample['metadata'].get('prev_chunk_preview'))}")
    print(f"\nContent preview:")
    print(new_sample['content'][:400] + "...\n")

    # Recommendations
    print("\n" + "=" * 80)
    print("💡 Recommendations")
    print("=" * 80)

    improvements = []

    if new_complete / len(new_chunks) > old_complete / len(old_chunks):
        improvements.append("✅ Better semantic integrity (more complete sections preserved)")

    if new_meta / len(new_chunks) > old_meta / len(old_chunks):
        improvements.append("✅ More complete metadata for better retrieval")

    if new_with_types > 0:
        improvements.append("✅ Content type detection for targeted retrieval")

    if new_with_context > 0:
        improvements.append("✅ Context windows for better understanding")

    # Check token consistency
    old_std = (sum((t - sum(old_tokens) / len(old_tokens)) ** 2 for t in old_tokens) / len(old_tokens)) ** 0.5
    new_std = (sum((t - sum(new_tokens) / len(new_tokens)) ** 2 for t in new_tokens) / len(new_tokens)) ** 0.5

    if new_std < old_std:
        improvements.append("✅ More consistent chunk sizes (better for embeddings)")

    if improvements:
        print("\n🎯 Enhanced Method Provides:")
        for imp in improvements:
            print(f"   {imp}")

    print(f"\n📝 To use enhanced method:")
    print(f"   python src/sgk_rag/core/document_processor_enhanced.py \\")
    print(f"      --input data/raw --output data/processed_enhanced \\")
    print(f"      --chunk-size 512 --chunk-overlap 50")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        compare_chunking()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
