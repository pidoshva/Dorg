"""Runtime detection of optional dependencies."""

import subprocess


class ClassifierCapabilities:
    def __init__(self):
        self.has_pillow = False
        self.has_ffprobe = False
        self.has_pdf_reader = False
        self._pdf_module = None

        try:
            from PIL import Image  # noqa: F401
            self.has_pillow = True
        except ImportError:
            pass

        try:
            subprocess.run(
                ["ffprobe", "-version"],
                capture_output=True, timeout=5,
            )
            self.has_ffprobe = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        try:
            import pikepdf  # noqa: F401
            self.has_pdf_reader = True
            self._pdf_module = "pikepdf"
        except ImportError:
            try:
                from PyPDF2 import PdfReader  # noqa: F401
                self.has_pdf_reader = True
                self._pdf_module = "PyPDF2"
            except ImportError:
                pass
