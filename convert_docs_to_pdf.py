#!/usr/bin/env python3
"""
Convert all .doc and .docx files in INPUT_FOLDER to PDF and move them
to OUTPUT_FOLDER. Existing .pdf files in INPUT_FOLDER are also moved
to OUTPUT_FOLDER. End result: OUTPUT_FOLDER contains only PDFs.
Uses LibreOffice headless for conversion.
"""

import shutil
import subprocess
import sys
from pathlib import Path

# ── Configure your folders here ──────────────────────────────────────────────
INPUT_FOLDER  = Path("~/Downloads/jfl/in").expanduser()
OUTPUT_FOLDER = Path("~/Downloads/jfl/out").expanduser()
# ─────────────────────────────────────────────────────────────────────────────


def convert_and_move(doc_path: Path) -> bool:
    """Convert a .doc/.docx file to PDF and move it to OUTPUT_FOLDER."""
    pdf_dest = OUTPUT_FOLDER / (doc_path.stem + ".pdf")

    if pdf_dest.exists():
        print(f"  [SKIP] PDF already exists in output: {pdf_dest.name}")
        return False

    print(f"  [CONVERTING] {doc_path.name}")
    result = subprocess.run(
        [
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            str(doc_path),
            "--outdir", str(OUTPUT_FOLDER),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"  [ERROR] Failed to convert {doc_path.name}")
        print(f"          {result.stderr.strip()}")
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

    total = len(doc_files) + len(pdf_files)
    if total == 0:
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
