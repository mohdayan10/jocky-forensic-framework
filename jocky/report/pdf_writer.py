"""Minimal PDF writer using only stdlib — no external dependencies.

Generates a valid PDF 1.4 document with text content, headers, and sections.
This avoids requiring reportlab/fpdf2/weasyprint for the demo.
"""

from __future__ import annotations

from typing import List


class PDFWriter:
    """Builds a valid PDF document from structured text content."""

    def __init__(self):
        self._objects: List[bytes] = []
        self._offsets: List[int] = []
        self._pages: List[int] = []
        self._page_contents: List[List[str]] = []
        self._current_page: List[str] = []
        self._line_y = 750
        self._font_size = 10
        self._lines_per_page = 60
        self._line_count = 0

    def add_title(self, text: str):
        self._add_text_line(text, size=16, bold=True)
        self._add_text_line("", size=10)

    def add_heading(self, text: str):
        self._add_text_line("", size=10)
        self._add_text_line(text, size=13, bold=True)
        self._add_text_line("-" * 60, size=10)

    def add_line(self, text: str, indent: int = 0):
        prefix = " " * indent
        safe = self._escape(prefix + text)
        self._add_text_line(safe, size=10)

    def add_blank(self):
        self._add_text_line("", size=10)

    def _add_text_line(self, text: str, size: int = 10, bold: bool = False):
        if self._line_count >= self._lines_per_page:
            self._finish_page()
            self._line_count = 0
            self._line_y = 750

        font = "/F2" if bold else "/F1"
        y = self._line_y
        safe = self._escape(text)
        self._current_page.append(
            f"BT {font} {size} Tf 50 {y} Td ({safe}) Tj ET"
        )
        self._line_y -= 13
        self._line_count += 1

    def _finish_page(self):
        if self._current_page:
            self._page_contents.append(self._current_page)
            self._current_page = []

    @staticmethod
    def _escape(text: str) -> str:
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def save(self, filepath: str):
        if self._current_page:
            self._finish_page()

        if not self._page_contents:
            return

        buf = bytearray()
        offsets = []

        def write(data: bytes):
            buf.extend(data)

        def add_obj(content: bytes) -> int:
            obj_num = len(offsets) + 1
            offsets.append(len(buf))
            write(f"{obj_num} 0 obj\n".encode())
            write(content)
            write(b"\nendobj\n")
            return obj_num

        write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        # Catalog (obj 1)
        cat_num = add_obj(b"<< /Type /Catalog /Pages 2 0 R >>")

        # Pages placeholder — will rewrite
        pages_offset_idx = len(offsets)
        pages_num = add_obj(b"PLACEHOLDER_PAGES")

        # Font objects
        f1_num = add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
        f2_num = add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier-Bold >>")

        resources = f"<< /Font << /F1 {f1_num} 0 R /F2 {f2_num} 0 R >> >>"

        page_obj_nums = []
        for page_lines in self._page_contents:
            stream_content = "\n".join(page_lines)
            stream_bytes = stream_content.encode("latin-1", errors="replace")
            stream_obj = add_obj(
                f"<< /Length {len(stream_bytes)} >>\nstream\n".encode()
                + stream_bytes
                + b"\nendstream"
            )

            page_obj = add_obj(
                f"<< /Type /Page /Parent {pages_num} 0 R "
                f"/MediaBox [0 0 612 792] "
                f"/Contents {stream_obj} 0 R "
                f"/Resources {resources} >>".encode()
            )
            page_obj_nums.append(page_obj)

        # Rewrite Pages object
        kids = " ".join(f"{p} 0 R" for p in page_obj_nums)
        pages_content = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_obj_nums)} >>"
        pages_start = offsets[pages_offset_idx]
        # We need to rebuild the buffer with correct Pages object
        # Simpler: rebuild from scratch
        buf2 = bytearray()
        offsets2 = []

        def write2(data: bytes):
            buf2.extend(data)

        def add_obj2(content: bytes) -> int:
            obj_num = len(offsets2) + 1
            offsets2.append(len(buf2))
            write2(f"{obj_num} 0 obj\n".encode())
            write2(content)
            write2(b"\nendobj\n")
            return obj_num

        write2(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        add_obj2(b"<< /Type /Catalog /Pages 2 0 R >>")
        add_obj2(b"PAGES_PLACEHOLDER")  # will patch
        f1 = add_obj2(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
        f2 = add_obj2(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier-Bold >>")

        resources2 = f"<< /Font << /F1 {f1} 0 R /F2 {f2} 0 R >> >>"
        page_nums2 = []

        for page_lines in self._page_contents:
            stream_content = "\n".join(page_lines)
            stream_bytes = stream_content.encode("latin-1", errors="replace")
            s = add_obj2(
                f"<< /Length {len(stream_bytes)} >>\nstream\n".encode()
                + stream_bytes
                + b"\nendstream"
            )
            p = add_obj2(
                f"<< /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 612 792] "
                f"/Contents {s} 0 R "
                f"/Resources {resources2} >>".encode()
            )
            page_nums2.append(p)

        # Now patch the Pages object (obj 2)
        kids2 = " ".join(f"{p} 0 R" for p in page_nums2)
        pages_bytes = f"<< /Type /Pages /Kids [{kids2}] /Count {len(page_nums2)} >>".encode()

        # Rebuild buf2 with correct pages
        final = bytearray()
        final_offsets = []

        def writef(data: bytes):
            final.extend(data)

        writef(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        obj_contents = []
        # obj 1: catalog
        obj_contents.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        # obj 2: pages (patched)
        obj_contents.append(pages_bytes)
        # obj 3: font 1
        obj_contents.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
        # obj 4: font 2
        obj_contents.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier-Bold >>")

        for page_lines in self._page_contents:
            stream_content = "\n".join(page_lines)
            sb = stream_content.encode("latin-1", errors="replace")
            obj_contents.append(
                f"<< /Length {len(sb)} >>\nstream\n".encode() + sb + b"\nendstream"
            )
            stream_num = len(obj_contents)
            resources_str = f"<< /Font << /F1 3 0 R /F2 4 0 R >> >>"
            obj_contents.append(
                f"<< /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 612 792] "
                f"/Contents {stream_num} 0 R "
                f"/Resources {resources_str} >>".encode()
            )

        page_obj_ids = []
        for i, content in enumerate(obj_contents):
            obj_num = i + 1
            final_offsets.append(len(final))
            writef(f"{obj_num} 0 obj\n".encode())
            writef(content)
            writef(b"\nendobj\n")
            # Track page objects (every second object after obj 4 is a page)
            if i >= 4 and (i - 4) % 2 == 1:
                page_obj_ids.append(obj_num)

        # Fix Pages kids
        kids_final = " ".join(f"{p} 0 R" for p in page_obj_ids)
        pages_fixed = f"<< /Type /Pages /Kids [{kids_final}] /Count {len(page_obj_ids)} >>".encode()

        # Rebuild one more time cleanly
        out = bytearray()
        out_offsets = []

        out.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        obj_data = []
        obj_data.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        obj_data.append(pages_fixed)
        obj_data.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
        obj_data.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier-Bold >>")

        page_ids = []
        for page_lines in self._page_contents:
            sc = "\n".join(page_lines)
            sb = sc.encode("latin-1", errors="replace")
            obj_data.append(
                f"<< /Length {len(sb)} >>\nstream\n".encode() + sb + b"\nendstream"
            )
            stream_id = len(obj_data)
            obj_data.append(
                f"<< /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 612 792] "
                f"/Contents {stream_id} 0 R "
                f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> >>".encode()
            )
            page_ids.append(len(obj_data))

        # Fix pages again
        kids_str = " ".join(f"{pid} 0 R" for pid in page_ids)
        obj_data[1] = f"<< /Type /Pages /Kids [{kids_str}] /Count {len(page_ids)} >>".encode()

        for i, data in enumerate(obj_data):
            num = i + 1
            out_offsets.append(len(out))
            out.extend(f"{num} 0 obj\n".encode())
            out.extend(data)
            out.extend(b"\nendobj\n")

        # Cross-reference table
        xref_offset = len(out)
        num_objs = len(out_offsets) + 1
        out.extend(b"xref\n")
        out.extend(f"0 {num_objs}\n".encode())
        out.extend(b"0000000000 65535 f \n")
        for off in out_offsets:
            out.extend(f"{off:010d} 00000 n \n".encode())

        # Trailer
        out.extend(b"trailer\n")
        out.extend(f"<< /Size {num_objs} /Root 1 0 R >>\n".encode())
        out.extend(b"startxref\n")
        out.extend(f"{xref_offset}\n".encode())
        out.extend(b"%%EOF\n")

        with open(filepath, "wb") as f:
            f.write(out)
