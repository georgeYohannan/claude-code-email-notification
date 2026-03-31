#!/usr/bin/env python3
"""
Convert all .doc and .docx files in INPUT_FOLDER to PDF and move them
to OUTPUT_FOLDER. Existing .pdf files in INPUT_FOLDER are also moved
to OUTPUT_FOLDER. End result: OUTPUT_FOLDER contains only PDFs.

Conversion backends (tried in order):
  1. LibreOffice headless (macOS/Linux) - install from https://www.libreoffice.org/
  2. docx2pdf (macOS only, requires Microsoft Word) - pip install docx2pdf
"""

import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ── Configure your folders here ──────────────────────────────────────────────
INPUT_FOLDER  = Path("~/Downloads/jfl/in").expanduser()
OUTPUT_FOLDER = Path("~/Downloads/jfl/out").expanduser()
# ─────────────────────────────────────────────────────────────────────────────

LIBREOFFICE_PATHS = [
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",  # macOS
    "/usr/bin/libreoffice",                                   # Linux
    "/usr/bin/soffice",                                       # Linux alt
    "/usr/local/bin/libreoffice",                             # Linux local
]
WORD_APP_PATH = Path("/Applications/Microsoft Word.app")


def find_libreoffice() -> Optional[str]:
    for path in LIBREOFFICE_PATHS:
        if Path(path).exists():
            return path
    return None


def check_requirements():
    """Ensure at least one conversion backend is available."""
    lo = find_libreoffice()
    if lo:
        return "libreoffice", lo

    if platform.system() == "Darwin" and WORD_APP_PATH.exists():
        try:
            from docx2pdf import convert  # noqa: F401
            return "docx2pdf", None
        except ImportError:
            print("Microsoft Word is installed but docx2pdf is missing.")
            print("Run: pip install docx2pdf")
            sys.exit(1)

    # Nothing found — give clear guidance
    print("Error: No conversion backend found.\n")
    if platform.system() == "Darwin":
        print("On macOS, install one of:")
        print("  • LibreOffice (free): https://www.libreoffice.org/")
        print("  • Microsoft Word + pip install docx2pdf")
    else:
        print("Install LibreOffice: https://www.libreoffice.org/")
    sys.exit(1)


def convert_with_libreoffice(doc_path: Path, lo_bin: str) -> bool:
    result = subprocess.run(
        [lo_bin, "--headless", "--convert-to", "pdf", str(doc_path), "--outdir", str(OUTPUT_FOLDER)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  [ERROR] {result.stderr.strip() or 'LibreOffice conversion failed'}")
        return False
    return True


def convert_with_docx2pdf(doc_path: Path) -> bool:
    from docx2pdf import convert
    pdf_dest = OUTPUT_FOLDER / (doc_path.stem + ".pdf")
    try:
        convert(str(doc_path), str(pdf_dest))
    except Exception as e:
        print(f"  [ERROR] {e or 'docx2pdf conversion failed (is Microsoft Word installed?)'}")
        return False
    return True


def convert_and_move(doc_path: Path, backend: str, lo_bin: Optional[str]) -> bool:
    """Convert a .doc/.docx file to PDF and save it in OUTPUT_FOLDER."""
    pdf_dest = OUTPUT_FOLDER / (doc_path.stem + ".pdf")

    if pdf_dest.exists():
        print(f"  [SKIP] PDF already exists in output: {pdf_dest.name}")
        return False

    print(f"  [CONVERTING] {doc_path.name}")

    if backend == "libreoffice":
        ok = convert_with_libreoffice(doc_path, lo_bin)
    else:
        ok = convert_with_docx2pdf(doc_path)

    if not ok:
        return False

    print(f"  [DONE] -> {pdf_dest.name}")
    return True


def move_pdf(pdf_path: Path) -> None:
    """Move an existing .pdf file to OUTPUT_FOLDER."""
    dest = OUTPUT_FOLDER / pdf_path.name
    if dest.exists():
        print(f"  [SKIP] Already in output: {pdf_path.name}")
        return
    shutil.move(str(pdf_path), str(dest))
    print(f"  [MOVED] {pdf_path.name} -> output folder")


def main():
    if not INPUT_FOLDER.is_dir():
        print(f"Error: INPUT_FOLDER '{INPUT_FOLDER}' does not exist or is not a directory.")
        sys.exit(1)

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    backend, lo_bin = check_requirements()
    print(f"Using backend: {backend}\n")

    doc_files = sorted(INPUT_FOLDER.rglob("*.doc")) + sorted(INPUT_FOLDER.rglob("*.docx"))
    pdf_files = sorted(INPUT_FOLDER.rglob("*.pdf"))

    if not doc_files and not pdf_files:
        print("No .doc, .docx, or .pdf files found in input folder.")
        return

    print(f"Found {len(doc_files)} Word file(s) and {len(pdf_files)} PDF file(s).\n")

    converted = skipped = failed = moved = 0

    if doc_files:
        print("--- Converting Word documents ---")
        for doc_path in doc_files:
            ok = convert_and_move(doc_path, backend, lo_bin)
            if ok:
                converted += 1
            else:
                pdf_dest = OUTPUT_FOLDER / (doc_path.stem + ".pdf")
                if pdf_dest.exists():
                    skipped += 1
                else:
                    failed += 1

    if pdf_files:
        print("\n--- Moving existing PDFs ---")
        for pdf_path in pdf_files:
            move_pdf(pdf_path)
            moved += 1

    print(f"\nDone.")
    print(f"  Converted : {converted}")
    print(f"  Skipped   : {skipped}")
    print(f"  Failed    : {failed}")
    print(f"  PDFs moved: {moved}")
    print(f"\nAll PDFs are in: {OUTPUT_FOLDER}")


if __name__ == "__main__":
    main()
