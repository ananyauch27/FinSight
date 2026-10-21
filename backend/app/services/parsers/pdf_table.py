import pdfplumber
import pandas as pd
from .base import BaseParser
from .generic_csv import GenericTabularParser, DATE_COLS, DESC_COLS


class PdfTableParser(BaseParser):
    bank_code = "generic_pdf"

    def can_parse(self, sample_text, filename):
        return filename.lower().endswith(".pdf")

    def parse(self, path, password=None):
        rows = []

        try:
            with pdfplumber.open(path, password=password or "") as pdf:
                for page in pdf.pages:
                    for table in page.extract_tables():
                        rows.extend(table)

        except Exception as e:
            if "password" in str(e).lower() or "encrypt" in str(e).lower():
                raise ValueError("Wrong or missing PDF password")
            raise

        if not rows:
            raise ValueError(
                "No tables found. Scanned (image) PDFs are not supported in the free version."
            )

        def norm(c):
            return str(c).replace("\n", " ").strip().lower() if c else ""

        header_idx = None

        for i, row in enumerate(rows):
            if (any(norm(c) in DATE_COLS for c in row)
                    and any(norm(c) in DESC_COLS for c in row)):
                header_idx = i
                break

        if header_idx is None:
            raise ValueError("Header row not found in PDF")

        header = [
            str(c).replace("\n", " ").strip() if c else f"col{i}"
            for i, c in enumerate(rows[header_idx])
        ]

        body = [
            r for r in rows[header_idx + 1:]
            if len(r) == len(header)
            and [norm(c) for c in r] != [norm(c) for c in rows[header_idx]]
        ]
        
        df = pd.DataFrame(body, columns=header)
        return GenericTabularParser().parse_dataframe(df)
