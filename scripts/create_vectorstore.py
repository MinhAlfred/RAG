import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sgk_rag.core.create_vectorstore import main


if __name__ == "__main__":
    main()

