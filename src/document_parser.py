from pathlib import Path

import pymupdf


def extract_pdf_text(pdf_path: Path) -> str:
    """
    Extract selectable text from a PDF proposal.
    """

    document = pymupdf.open(pdf_path)

    pages = []

    for page_number, page in enumerate(document, start=1):
        text = page.get_text("text")

        pages.append(
            f"\n--- PAGE {page_number} ---\n{text.strip()}"
        )

    document.close()

    return "\n".join(pages).strip()

if __name__ == "__main__":
    #pdf_path = Path("data/test_pdfs/proposal_001.pdf")
    pdf_path = Path("data/test_pdfs/DE-0426-1002-1017-1075.pdf")

    extracted_text = extract_pdf_text(pdf_path)

    print(extracted_text[:50000])