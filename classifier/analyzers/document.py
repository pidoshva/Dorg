"""Document analysis: PDF page count, size-per-page ratio."""

import os
from ..signals import AnalysisContext, Signal
from ..capabilities import ClassifierCapabilities
from ..taxonomy import *  # noqa: F403, F401


def analyze(ctx: AnalysisContext, caps: ClassifierCapabilities):
    """Analyze document files."""
    ext = ctx.extension

    # Direct subtype from extension for office formats
    if ext in ("doc", "docx", "odt", "rtf", "pages"):
        ctx.signals.append(Signal("office_word_ext", ext, {DOC_OFFICE_WORD: 0.5}))
    elif ext in ("xls", "xlsx", "ods", "csv", "numbers"):
        ctx.signals.append(Signal("office_spreadsheet_ext", ext, {DOC_OFFICE_SPREADSHEET: 0.5}))
    elif ext in ("ppt", "pptx", "odp", "keynote"):
        ctx.signals.append(Signal("office_presentation_ext", ext, {DOC_OFFICE_PRESENTATION: 0.5}))
    elif ext in ("epub", "mobi"):
        ctx.signals.append(Signal("ebook_ext", ext, {DOC_EBOOK: 0.6}))
    elif ext == "txt":
        size = ctx.file_size
        if size < 50_000:
            ctx.signals.append(Signal("small_text", size, {DOC_TEXT_NOTE: 0.4}))
        else:
            ctx.signals.append(Signal("large_text", size, {DOC_TEXT_LOG: 0.2, DOC_TEXT_NOTE: 0.1}))
    elif ext == "log":
        ctx.signals.append(Signal("log_ext", ext, {DOC_TEXT_LOG: 0.5}))

    # PDF analysis
    if ext == "pdf" or (ctx.magic_type and ctx.magic_type == "application/pdf"):
        _analyze_pdf(ctx, caps)


def _analyze_pdf(ctx: AnalysisContext, caps: ClassifierCapabilities):
    """Extract PDF page count and compute size-per-page ratio."""
    page_count = None

    if caps.has_pdf_reader:
        try:
            if caps._pdf_module == "pikepdf":
                import pikepdf
                with pikepdf.open(ctx.path) as pdf:
                    page_count = len(pdf.pages)
            else:
                from PyPDF2 import PdfReader
                reader = PdfReader(str(ctx.path))
                page_count = len(reader.pages)
        except Exception:
            pass

    if page_count is not None and page_count > 0:
        ctx.metadata["pdf_pages"] = page_count
        size_per_page = ctx.file_size / page_count
        ctx.metadata["pdf_size_per_page"] = round(size_per_page)

        if page_count > 50:
            ctx.signals.append(Signal("pdf_many_pages", page_count, {
                DOC_PDF_EBOOK: 0.35,
            }))
        elif page_count <= 5:
            ctx.signals.append(Signal("pdf_few_pages", page_count, {
                DOC_PDF: 0.15,
            }))

        if size_per_page > 500_000:
            ctx.signals.append(Signal("pdf_image_heavy", size_per_page, {
                DOC_PDF_SCANNED: 0.35,
            }))
        elif size_per_page < 50_000:
            ctx.signals.append(Signal("pdf_text_light", size_per_page, {
                DOC_PDF_EBOOK: 0.2,
            }))
    else:
        # No page count — just generic PDF
        ctx.signals.append(Signal("pdf_generic", True, {DOC_PDF: 0.3}))
