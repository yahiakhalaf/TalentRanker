from pathlib import Path
from docling.document_converter import DocumentConverter

import pymupdf
import pytesseract
from PIL import Image
import io



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





def convert_files_to_markdown_with_ocr(input_dir: str, output_dir: str, subdir_name: str):
    """
    Convert files from various formats to markdown using PyMuPDF and OCR.

    Args:
        input_dir (str): Directory containing files to convert.
        output_dir (str): Base directory where converted markdown files will be saved.
        subdir_name (str): Name of the subdirectory to store markdown files.

    Returns:
        None
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"Input directory not found: {input_dir}")
        return
    if not input_path.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")

    output_path = Path(output_dir) / subdir_name
    output_path.mkdir(parents=True, exist_ok=True)

    supported_exts = [".pdf", ".png", ".jpg", ".jpeg"]
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
        
        full_text = ""
        file_extension = file.suffix.lower()
        
        try:
            print(f"Processing: {file.name}")
            if file_extension == '.pdf':
                # Handle PDF files
                with pymupdf.open(str(file)) as doc:
                    for page_num, page in enumerate(doc):
                        text = page.get_text()
                        if text.strip():
                            full_text += text
                        else:
                            print(f"  No selectable text found on page {page_num + 1}. Running OCR...")
                            pix = page.get_pixmap()
                            img = Image.open(io.BytesIO(pix.tobytes("png")))
                            full_text += pytesseract.image_to_string(img)
            
            # Handle image files
            elif file_extension in ['.jpg', '.jpeg', '.png']:
                full_text = pytesseract.image_to_string(Image.open(str(file)))

            # Save the extracted text to a markdown file
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(full_text)
                
        except Exception as e:
            print(f"  Error processing {file.name}: {str(e)}")
            failed_conversions += 1
            continue

    print(f"\nParsing completed! {failed_conversions} files failed, {skipped_files} skipped, {len(files_to_process) - failed_conversions - skipped_files} processed successfully.")