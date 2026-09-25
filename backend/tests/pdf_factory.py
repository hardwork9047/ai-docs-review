"""Build tiny, valid PDFs in tests (Helvetica text at chosen sizes, optional image).

実資料に依存せず pdfplumber / pdfium の読み取りを検証するための最小 PDF 生成器。
"""

WIDTH, HEIGHT = 720, 405  # 16:9 のスライド相当(pt)

Line = tuple[str, float]  # (text, font size pt)


def make_pdf(pages: list[list[Line]], images_per_page: list[int] | None = None) -> bytes:
    """Return PDF bytes with one page per entry; each line is drawn top-down."""
    images = images_per_page or [0] * len(pages)
    objects: list[bytes] = []

    def add(body: bytes) -> int:
        objects.append(body)
        return len(objects)

    catalog = add(b"")  # placeholder, filled after pages are known
    pages_obj = add(b"")
    font = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    image = add(
        b"<< /Type /XObject /Subtype /Image /Width 1 /Height 1 /ColorSpace /DeviceGray"
        b" /BitsPerComponent 8 /Length 1 >>\nstream\n\x80\nendstream"
    )

    kids = []
    for lines, n_images in zip(pages, images, strict=True):
        ops = []
        y = HEIGHT - 60
        for text, size in lines:
            ops.append(f"BT /F1 {size} Tf 40 {y} Td ({text}) Tj ET")
            y -= int(size * 1.6)
        for i in range(n_images):
            ops.append(f"q 80 0 0 80 {400 + i * 90} 40 cm /Im1 Do Q")
        stream = "\n".join(ops).encode()
        content = add(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream))
        page = add(
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] /Contents %d 0 R"
            b" /Resources << /Font << /F1 %d 0 R >> /XObject << /Im1 %d 0 R >> >> >>"
            % (pages_obj, WIDTH, HEIGHT, content, font, image)
        )
        kids.append(page)

    objects[catalog - 1] = b"<< /Type /Catalog /Pages %d 0 R >>" % pages_obj
    kid_refs = b" ".join(b"%d 0 R" % k for k in kids)
    objects[pages_obj - 1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (kid_refs, len(kids))

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n%s\nendobj\n" % (i, body)
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % off for off in offsets)
    out += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        catalog,
        xref,
    )
    return bytes(out)
