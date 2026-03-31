#!/usr/bin/env python3
"""
Convert all .doc and .docx files in a folder (recursively) to PDF.
Skips files that already have a corresponding PDF.
Uses LibreOffice headless for conversion.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def convert_to_pdf(doc_path: Path, output_dir: Path) -> bool:
    """Convert a single .doc/.docx file to PDF using LibreOffice."""
    pdf_path = output_dir / (doc_path.stem + ".pdf")

    if pdf_path.exists():
        print(f"  [SKIP] PDF already exists: {pdf_path}")
        return False

    print(f"  [CONVERTING] {doc_path} -> {pdf_path}")
    result = subprocess.run(
        [
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            str(doc_path),
            "--outdir", str(output_dir),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"  [ERROR] Failed to convert {doc_path}")
        print(f"          {result.stderr.strip()}")
        return False

    print(f"  [DONE] {pdf_path.name}")
    return True


def process_folder(folder: Path, same_dir: bool) -> None:
    """Walk folder recursively and convert all .doc/.docx files."""
    doc_files = list(folder.rglob("*.doc")) + list(folder.rglob("*.docx"))

    if not doc_files:
        print("No .doc or .docx files found.")
        return

    print(f"Found {len(doc_files)} file(s) to process.\n")

    converted = 0
    skipped = 0
    failed = 0

    for doc_path in sorted(doc_files):
        output_dir = doc_path.parent if same_dir else folder
        result = convert_to_pdf(doc_path, output_dir)
        if result is True:
            converted += 1
        elif result is False:
            # Distinguish skip vs error by checking if pdf now exists
            pdf_path = output_dir / (doc_path.stem + ".pdf")
            if pdf_path.exists():
                skipped += 1 if not result else converted
            else:
                failed += 1

    print(f"\nDone. Converted: {converted} | Skipped: {skipped} | Failed: {failed}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert .doc/.docx files to PDF using LibreOffice."
    )
    parser.add_argument(
        "folder",
        type=Path,
        help="Path to the folder containing documents",
    )
    parser.add_argument(
        "--same-dir",
        action="store_true",
        default=True,
        help="Save each PDF in the same directory as its source file (default: true)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Save all PDFs to a specific output directory instead",
    )
    args = parser.parse_args()

    folder = args.folder.resolve()
    if not folder.is_dir():
        print(f"Error: '{folder}' is not a valid directory.")
        sys.exit(1)

    # If explicit output dir is given, use that; otherwise save alongside source
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        same_dir = False

        # Override process_folder to use fixed output dir
        doc_files = list(folder.rglob("*.doc")) + list(folder.rglob("*.docx"))
        if not doc_files:
            print("No .doc or .docx files found.")
            return

        print(f"Found {len(doc_files)} file(s) to process.\n")
        converted = skipped = failed = 0
        for doc_path in sorted(doc_files):
            ok = convert_to_pdf(doc_path, args.output_dir)
            if ok:
                converted += 1
            else:
                pdf_path = args.output_dir / (doc_path.stem + ".pdf")
                if pdf_path.exists():
                    skipped += 1
                else:
                    failed += 1
        print(f"\nDone. Converted: {converted} | Skipped: {skipped} | Failed: {failed}")
    else:
        process_folder(folder, same_dir=True)


if __name__ == "__main__":
    main()
