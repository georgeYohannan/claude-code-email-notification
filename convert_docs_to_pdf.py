#!/usr/bin/env python3
"""
Convert all .doc and .docx files in INPUT_FOLDER to PDF and move them
to OUTPUT_FOLDER. Existing .pdf files in INPUT_FOLDER are also moved
to OUTPUT_FOLDER. End result: OUTPUT_FOLDER contains only PDFs.

Requires: pip install docx2pdf
  - On macOS: uses Microsoft Word (must be installed) via AppleScript
  - On Linux: uses LibreOffice (must be installed)
"""

import shutil
import sys
from pathlib import Path

try:
    from docx2pdf import convert
except ImportError:
    print("Error: docx2pdf is not installed. Run: pip install docx2pdf")
    sys.exit(1)

# ── Configure your folders here ──────────────────────────────────────────────
INPUT_FOLDER  = Path("~/Downloads/jfl/in").expanduser()
OUTPUT_FOLDER = Path("~/Downloads/jfl/out").expanduser()
# ─────────────────────────────────────────────────────────────────────────────


def convert_and_move(doc_path: Path) -> bool:
    """Convert a .doc/.docx file to PDF and save it in OUTPUT_FOLDER."""
    pdf_dest = OUTPUT_FOLDER / (doc_path.stem + ".pdf")

    if pdf_dest.exists():
        print(f"  [SKIP] PDF already exists in output: {pdf_dest.name}")
        return False

    print(f"  [CONVERTING] {doc_path.name}")
    try:
        convert(str(doc_path), str(pdf_dest))
    except Exception as e:
        print(f"  [ERROR] Failed to convert {doc_path.name}: {e}")
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
            ok = convert_and_move(doc_path)
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
