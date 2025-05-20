import fitz  # PyMuPDF
from pdfminer.high_level import extract_text as pdfminer_extract
from PIL import Image
import pytesseract
import pdfplumber
import io
import os

def extract_text_and_images(pdf_path):
    if not os.path.isfile(pdf_path):
        raise ValueError("Invalid PDF path")

    base_name = os.path.splitext(os.path.basename(pdf_path))[0]

    # Create output folders
    image_dir = "../uploads/extracted_images"
    text_dir = "../extract_raw_text"
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(text_dir, exist_ok=True)

    # Output text file
    text_file_path = os.path.join(text_dir, f"{base_name}.txt")

    with open(text_file_path, "w", encoding="utf-8") as text_file:
        # --- Pure text ---
        print("[INFO] Extracting pure text...")
        pure_text = pdfminer_extract(pdf_path)
        text_file.write("Pure Text:\n")
        text_file.write(pure_text.strip() + "\n\n")

        # --- Tables ---
        print("[INFO] Extracting tables...")
        with pdfplumber.open(pdf_path) as pdf:
            table_count = 1
            for page_num, page in enumerate(pdf.pages, 1):
                tables = page.extract_tables()
                for table in tables:
                    if not table: continue
                    text_file.write(f"Table {table_count} (Page {page_num}):\n")
                    for row in table:
                        line = ', '.join([cell.strip() if cell else "" for cell in row])
                        text_file.write(line + "\n")
                    text_file.write("\n")
                    table_count += 1

        # --- Images and OCR ---
        print("[INFO] Extracting images and performing OCR...")
        doc = fitz.open(pdf_path)
        img_count = 1

        for page_index in range(len(doc)):
            for img_index, img in enumerate(doc.get_page_images(page_index)):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]

                # Save image
                image_filename = f"{base_name}_{img_count}.{ext}"
                image_path = os.path.join(image_dir, image_filename)
                with open(image_path, "wb") as f:
                    f.write(image_bytes)

                # OCR the image
                img_obj = Image.open(io.BytesIO(image_bytes))
                ocr_text = pytesseract.image_to_string(img_obj)

                # Write OCR result to text file
                text_file.write(f"Image Text {img_count}:\n")
                text_file.write(ocr_text.strip() + "\n\n")

                img_count += 1

        print(f"[INFO] Extraction complete. Text saved to '{text_file_path}'.")
        print(f"[INFO] {img_count - 1} image(s) saved to '{image_dir}'.")

if __name__ == "__main__":
    pdf_path = "../uploads/FTL Bill.pdf"
    try:
        extract_text_and_images(pdf_path)
    except Exception as e:
        print(f"[ERROR] {e}")
