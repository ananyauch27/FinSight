from .generic_csv import GenericTabularParser
from .pdf_table import PdfTableParser
# from .banks.hdfc import HdfcPdfParser

PARSERS = [
    # HdfcPdfParser(),     # bank-specific parsers first
    GenericTabularParser(),
    PdfTableParser(),
]

def pick_parser(filename: str, sample_text: str = ""):
    for p in PARSERS:
        if p.can_parse(sample_text, filename):
            return p
    raise ValueError("Unsupported file type")