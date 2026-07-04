# PdfReader is the pypdf class that knows how to open and parse a PDF file.
from pypdf import PdfReader


def extract_text_from_pdf(pdf_path):
    # Open the PDF and get an object we can loop through, page by page.
    reader = PdfReader(pdf_path)

    page_texts = []
    for page in reader.pages:
        # Pull the readable text out of this one page.
        text = page.extract_text()
        # Scanned/image-only or blank pages return None or "" here —
        # skip them instead of crashing later when we try to join None.
        if text:
            page_texts.append(text)

    # Join every page's text into one string, with a blank line between
    # pages so the end of one page doesn't run into the start of the next.
    return "\n\n".join(page_texts)


if __name__ == "__main__":
    # This block only runs when the file is executed directly
    # (e.g. `python extract.py myfile.pdf`), not when it's imported.
    import sys

    path = sys.argv[1]
    print(extract_text_from_pdf(path))
