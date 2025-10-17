import sys
import argparse
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from config.logging_config import setup_logging
from src.sgk_rag.core.document_processor import DocumentProcessor
from src.sgk_rag.utils.file_utils import get_pdf_files

logger = setup_logging(log_level="INFO", log_dir=settings.LOG_DIR)


def list_supported_subjects():
    """List all supported subjects"""
    print("\n📚 Supported Subjects:")
    print("=" * 70)
    for key, config in settings.SUPPORTED_SUBJECTS.items():
        print(f"  {key:15s} → {config['name']}")
        print(f"                  Aliases: {', '.join(config['aliases'][:3])}")
    print("=" * 70)


def process_single_subject(
        input_path: Path,
        subject: str,
        output_dir: Path,
        chunk_size: int,
        chunk_overlap: int
):
    """Process PDFs for a single subject"""

    # Initialize processor
    processor = DocumentProcessor(
        subject=subject,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    # Get PDF files
    if input_path.is_file():
        pdf_files = [input_path]
    elif input_path.is_dir():
        pdf_files = get_pdf_files(input_path)
    else:
        logger.error(f"Invalid input: {input_path}")
        return []

    if not pdf_files:
        logger.warning(f"No PDF files found in {input_path}")
        return []

    logger.info(f"\n{'=' * 70}")
    logger.info(f"📖 Processing {len(pdf_files)} PDFs for subject: {subject or 'AUTO'}")
    logger.info(f"{'=' * 70}\n")

    all_chunks = []

    for idx, pdf_file in enumerate(pdf_files, 1):
        logger.info(f"[{idx}/{len(pdf_files)}] {pdf_file.name}")
        logger.info(f"{'─' * 70}")

        try:
            chunks = processor.process_pdf(
                pdf_file,
                output_dir=output_dir,
                subject=subject
            )
            all_chunks.extend(chunks)

            # Print statistics
            stats = processor.get_statistics(chunks)
            logger.info(f"\n   📊 Statistics:")
            logger.info(f"      - Subject: {stats.get('subject', 'N/A')}")
            logger.info(f"      - Chunks: {stats['total_chunks']}")
            logger.info(f"      - Tokens: {stats['total_tokens']:,}")
            logger.info(f"      - Pages: {stats['pages']}")
            logger.info(f"      - Chapters: {stats['chapters']}")
            if stats.get('has_formula', 0) > 0:
                logger.info(f"      - Has formulas: {stats['has_formula']} chunks")
            if stats.get('has_code', 0) > 0:
                logger.info(f"      - Has code: {stats['has_code']} chunks")

        except Exception as e:
            logger.error(f"   ❌ Error: {e}", exc_info=True)
            continue

    return all_chunks


def organize_by_subject(data_dir: Path) -> dict:
    """Organize PDFs by subject in subdirectories"""

    organized = {}
    pdf_files = get_pdf_files(data_dir)

    if not pdf_files:
        return organized

    logger.info("\n🔍 Analyzing PDF files...")

    for pdf_file in pdf_files:
        # Try to detect subject
        subject = settings.detect_subject_from_filename(pdf_file.name)

        if subject:
            if subject not in organized:
                organized[subject] = []
            organized[subject].append(pdf_file)
            logger.info(f"   {pdf_file.name} → {subject}")
        else:
            logger.warning(f"   {pdf_file.name} → Unknown subject")
            if 'unknown' not in organized:
                organized['unknown'] = []
            organized['unknown'].append(pdf_file)

    return organized


def main():
    parser = argparse.ArgumentParser(
        description="Process PDF textbooks into chunks - Multi-Subject Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single file (auto-detect subject)
  python scripts/process_pdfs.py data/raw/SGK_TinHoc_Lop10.pdf

  # Process single file with specific subject
  python scripts/process_pdfs.py data/raw/toan10.pdf --subject toan

  # Process all PDFs in directory (auto-organize by subject)
  python scripts/process_pdfs.py data/raw/ --auto-organize

  # Process specific subject folder
  python scripts/process_pdfs.py data/raw/tin_hoc/ --subject tin_hoc

  # List supported subjects
  python scripts/process_pdfs.py --list-subjects
        """
    )

    parser.add_argument(
        "input",
        type=str,
        nargs='?',
        help="Input PDF file or directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory (default: data/processed/)"
    )
    parser.add_argument(
        "--subject",
        type=str,
        default=None,
        help="Subject key (tin_hoc, toan, ly, etc.). Auto-detect if not specified"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=800,
        help="Chunk size in characters (default: 800)"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=150,
        help="Chunk overlap in characters (default: 150)"
    )
    parser.add_argument(
        "--auto-organize",
        action="store_true",
        help="Auto-organize PDFs by detected subject"
    )
    parser.add_argument(
        "--list-subjects",
        action="store_true",
        help="List all supported subjects"
    )

    args = parser.parse_args()

    # List subjects and exit
    if args.list_subjects:
        list_supported_subjects()
        return

    # Validate input
    if not args.input:
        parser.print_help()
        return

    # Setup paths
    input_path = Path(args.input)
    output_dir = Path(args.output) if args.output else settings.PROCESSED_DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        return

    # Main processing logic
    if args.auto_organize and input_path.is_dir():
        # Auto-organize by subject
        logger.info("\n" + "=" * 70)
        logger.info("🚀 AUTO-ORGANIZE MODE: Processing by subject")
        logger.info("=" * 70)

        organized = organize_by_subject(input_path)

        if not organized:
            logger.error("No PDF files found")
            return

        logger.info(f"\nFound {len(organized)} subject(s)")

        all_chunks_total = []

        for subject_key, pdf_files in organized.items():
            if subject_key == 'unknown':
                logger.warning(f"\n⚠️  Skipping {len(pdf_files)} files with unknown subject")
                continue

            logger.info(f"\n{'=' * 70}")
            logger.info(f"📚 Processing Subject: {subject_key.upper()}")
            logger.info(f"{'=' * 70}")

            # Create subject-specific output directory
            subject_output_dir = output_dir / subject_key
            subject_output_dir.mkdir(exist_ok=True)

            # Process files for this subject
            chunks = process_single_subject(
                input_path,
                subject_key,
                subject_output_dir,
                args.chunk_size,
                args.chunk_overlap
            )

            all_chunks_total.extend(chunks)

            logger.info(f"\n✅ {subject_key}: {len(chunks)} chunks created")

        # Final summary
        logger.info(f"\n{'=' * 70}")
        logger.info(f"✅ ALL SUBJECTS COMPLETED!")
        logger.info(f"{'=' * 70}")
        logger.info(f"   Total chunks: {len(all_chunks_total):,}")
        logger.info(f"   Output: {output_dir}/")

    else:
        # Process single subject
        chunks = process_single_subject(
            input_path,
            args.subject,
            output_dir,
            args.chunk_size,
            args.chunk_overlap
        )

        logger.info(f"\n{'=' * 70}")
        logger.info(f"✅ COMPLETED!")
        logger.info(f"{'=' * 70}")
        logger.info(f"   Total chunks: {len(chunks):,}")
        logger.info(f"   Output: {output_dir}/")

    logger.info(f"\n💡 Next step: Create vector store")
    logger.info(f"   python scripts/create_vectorstore.py")


if __name__ == "__main__":
    main()