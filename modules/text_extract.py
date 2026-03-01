# ===============================
# OCR TEXT EXTRACTION MODULE
# ===============================

import pytesseract
from pdf2image import convert_from_path
from pathlib import Path
import os
import re
from PIL import Image


POPPLER_PATH = r"C:\poppler\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# -------------------------------
# UTIL: Normalize spacing
# -------------------------------

def normalize_spacing(text: str) -> str:
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = re.sub(r'\n{3,}', '\n', text)
    return text.strip()


# -------------------------------
# MAIN OCR FUNCTION
# -------------------------------

def run_ocr(pdf_path: str, output_txt_path: str) -> str:

    print(f"\n📄 Converting PDF to images: {pdf_path}")

    try:
        images = convert_from_path(
            pdf_path,
            dpi=300,
            poppler_path=POPPLER_PATH
        )
    except Image.DecompressionBombError:
        raise Exception(
            "PDF resolution too high. "
            "Please rescan at 300 DPI (A4 size) and try again."
        )
    except Exception as e:
        raise Exception(f"OCR failed during PDF conversion: {str(e)}")

    print(f"Total pages detected: {len(images)}")

    all_pages_text = []

    for idx, img in enumerate(images):
        print(f"OCR processing page {idx + 1}...")

        page_text = pytesseract.image_to_string(
            img,
            lang="eng",
            config="--psm 6"
        )

        all_pages_text.append(
            f"\n\n"
            + page_text +
            f"\n\n"
        )

    os.makedirs(Path(output_txt_path).parent, exist_ok=True)

    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write("".join(all_pages_text))

    final_text = normalize_spacing("".join(all_pages_text))

    print(f"✅ OCR completed. Output saved to:\n{output_txt_path}")

    return final_text