import os
from pathlib import Path
from docling.document_converter import DocumentConverter


def convert_files_to_markdown(input_dir: str, output_dir: str, subdir_name: str):
    """
    Convert files from various formats to markdown using docling.

    Args:
        input_dir (str): Directory containing files to convert.
        output_dir (str): Base directory where converted markdown files will be saved.
        subdir_name (str): Name of the subdirectory to store markdown files.

    Returns:
        None
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        return
    if not input_path.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")

    output_path = Path(output_dir) / subdir_name
    output_path.mkdir(parents=True, exist_ok=True)

    converter = DocumentConverter()
    supported_exts = [".pdf", ".png", ".jpg", ".jpeg", ".docx", ".txt"]
    files_to_process = [
        file for file in input_path.iterdir()
        if file.is_file() and file.suffix.lower() in supported_exts
    ]

    if not files_to_process:
        print("No supported files found to process.")
        return

    print(f"Found {len(files_to_process)} files to process")
    failed_conversions = 0
    skipped_files = 0
    for file in files_to_process:
        md_file = output_path / f"{file.stem}.md"
        if md_file.exists():
            print(f"Skipping (already converted): {md_file.name}")
            skipped_files += 1
            continue
        try:
            print(f"Processing: {file.name}")
            result = converter.convert(str(file)).document
            md_content = result.export_to_markdown(image_placeholder='')
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(md_content)
        except Exception as e:
            print(f"Error processing {file.name}: {str(e)}")
            failed_conversions += 1
            continue

    print(f"\nParsing completed! {failed_conversions} files failed, {skipped_files} skipped, {len(files_to_process) - failed_conversions - skipped_files} processed successfully.")