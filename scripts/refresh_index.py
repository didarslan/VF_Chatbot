from __future__ import annotations

"""
Basit refresh: Chroma kullanıyorsan en temiz yöntem directory'i silip yeniden build etmek.
Milvus/Zilliz için upsert ile çalışabilirsin.
"""

import os
import sys
from pathlib import Path
from shutil import rmtree

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from vfa.core.config import settings


def main() -> None:
    if settings.vector_backend.lower() == "chroma":
        chroma_dir = Path(settings.chroma_dir)
        if chroma_dir.exists():
            rmtree(chroma_dir)
            print("[OK] removed chroma dir:", chroma_dir)
        else:
            print("[SKIP] chroma dir not found:", chroma_dir)

    # rebuild
    from scripts.build_index import main as build_main
    build_main()


if __name__ == "__main__":
    main()
