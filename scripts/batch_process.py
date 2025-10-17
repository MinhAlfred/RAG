"""Batch processing script for organized folder structure"""

import sys
from pathlib import Path
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from config.logging_config import setup_logging
from src.sgk_rag.core.document_processor import DocumentProcessor
from src.sgk_rag.utils.file_utils import get_pdf_files

logger = setup_logging(log_level="INFO", log_dir=settings.LOG_DIR)


def batch_process_organized_structure(root_dir: Path, output_dir: Path):
    """
    Process organized folder structure:

    data/raw/
    ├── tin_hoc/
    │   ├── lop_10.pdf
    │   └── lop_11.pdf
    ├── toan/
    │   ├── lop_10.pdf
    │   └── lop_11.pdf
    └── ly/
        └── lop_12.pdf
    """

    logger.info(f"\n{'=' * 70}")
    logger.info(f"🚀 BATCH PROCESSING - Organized Structure")
    logger.info(f"{'=' * 70}\n")

    # Find subject folders
    subject_folders = [d for d in root_dir.iterdir() if d.is_dir()]

    if not subject_folders:
        logger.error(f"No subject folders found in {root_dir}")
        return

    logger.info(f"Found {len(subject_folders)} subject folders:")
    for folder in subject_folders:
        pdf_count = len(list(folder.glob("*.pdf")))
        logger.info(f"   📁 {folder.name}: {pdf_count} PDFs")

    total_chunks = 0

    for subject_folder in subject_folders:
        subject_key = subject_folder.name

        # Check if subject is supported
        if subject_key not in settings.SUPPORTED_SUBJECTS:
            logger.warning(f"\n⚠️  Unknown subject: {subject_key}, skipping...")
            continue

        logger.info(f"\n{'=' * 70}")
        logger.info(f"📚 Processing: {subject_key.upper()}")
        logger.info(f"{'=' * 70}")

        # Get PDFs
        pdf_files = get_pdf_files(subject_folder)

        if not pdf_files:
            logger.warning(f"   No PDFs found in {subject_folder}")
            continue

        # Create processor
        processor = DocumentProcessor(subject=subject_key)

        # Create output directory
        subject_output_dir = output_dir / subject_key
        subject_output_dir.mkdir(parents=True, exist_ok=True)

        # Process each PDF
        subject_chunks = 0

        for idx, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"\n   [{idx}/{len(pdf_files)}] {pdf_file.name}")

            try:
                chunks = processor.process_pdf(pdf_file, subject_output_dir)
                subject_chunks += len(chunks)

                stats = processor.get_statistics(chunks)
                logger.info(f"      ✓ {len(chunks)} chunks, {stats['total_tokens']:,} tokens")

            except Exception as e:
                logger.error(f"      ❌ Error: {e}")
                continue

        logger.info(f"\n   ✅ {subject_key}: {subject_chunks} total chunks")
        total_chunks += subject_chunks

    # Final summary
    logger.info(f"\n{'=' * 70}")
    logger.info(f"✅ BATCH PROCESSING COMPLETED!")
    logger.info(f"{'=' * 70}")
    logger.info(f"   Total subjects: {len(subject_folders)}")
    logger.info(f"   Total chunks: {total_chunks:,}")
    logger.info(f"   Output: {output_dir}/")


def main():
    parser = argparse.ArgumentParser(
        description="Batch process organized subject folders"
    )
    parser.add_argument(
        "input",
        type=str,
        help="Root directory containing subject folders"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory"
    )

    args = parser.parse_args()

    root_dir = Path(args.input)
    output_dir = Path(args.output) if args.output else settings.PROCESSED_DATA_DIR

    if not root_dir.exists():
        logger.error(f"Directory not found: {root_dir}")
        return

    batch_process_organized_structure(root_dir, output_dir)


if __name__ == "__main__":
    main()
