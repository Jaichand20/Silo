from pypdf import PdfReader


def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)

    page_texts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            page_texts.append(text)

    return "\n\n".join(page_texts)


if __name__ == "__main__":
    import sys

    path = sys.argv[1]
    print(extract_text_from_pdf(path))
