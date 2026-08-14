"""
EPUB Document Exporter rendering DocumentIR into standard EPUB ebook archives.
"""

import io
import logging
from typing import Optional
import zipfile

from scandoc.exporters.base import BaseExporter
from scandoc.exporters.html_exporter import HtmlExporter
from scandoc.exporters.models import ExportOptions, ExportResult
from scandoc.exporters.taxonomy import OutputDestination
from scandoc.models import DocumentIR

logger = logging.getLogger("scandoc.exporters.epub")


class EpubExporter(BaseExporter):
    """
    EPUB Document Exporter generating compliant EPUB ebook zip archives.
    """

    @property
    def format_id(self) -> str:
        return "epub"

    @property
    def description(self) -> str:
        return "EPUB ebook document archive exporter"

    @property
    def file_extension(self) -> str:
        return "epub"

    def export(
        self,
        document: DocumentIR,
        options: Optional[ExportOptions] = None,
    ) -> ExportResult:
        opts = options or ExportOptions(format_id="epub")
        title = document.metadata.title or document.metadata.name or "scanDOC Document"

        # 1. Render XHTML content using HtmlExporter
        html_exp = HtmlExporter()
        html_res = html_exp.export(document, options=opts)
        body_xhtml = str(html_res.content)

        # 2. Build EPUB zip structure in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 2a. mimetype (must be first, uncompressed)
            zip_file.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

            # 2b. META-INF/container.xml
            container_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
                '  <rootfiles>\n'
                '    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n'
                '  </rootfiles>\n'
                '</container>'
            )
            zip_file.writestr("META-INF/container.xml", container_xml)

            # 2c. OEBPS/styles.css
            styles_css = (
                "body { font-family: sans-serif; line-height: 1.6; margin: 1em; }\n"
                "h1, h2, h3 { color: #111827; margin-top: 1.5em; }\n"
                "p { margin-bottom: 1em; text-align: justify; }\n"
                "table { width: 100%; border-collapse: collapse; margin: 1em 0; }\n"
                "th, td { border: 1px solid #d1d5db; padding: 0.5em; text-align: left; }\n"
            )
            zip_file.writestr("OEBPS/styles.css", styles_css)

            # 2d. OEBPS/chapter1.xhtml
            chapter_xhtml = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'
                '<html xmlns="http://www.w3.org/1999/xhtml">\n'
                '<head>\n'
                f'  <title>{title}</title>\n'
                '  <link rel="stylesheet" type="text/css" href="styles.css"/>\n'
                '</head>\n'
                '<body>\n'
                f'{body_xhtml}\n'
                '</body>\n'
                '</html>'
            )
            zip_file.writestr("OEBPS/chapter1.xhtml", chapter_xhtml)

            # 2e. OEBPS/content.opf
            content_opf = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookID" version="2.0">\n'
                '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
                f'    <dc:title>{title}</dc:title>\n'
                '    <dc:language>en</dc:language>\n'
                '    <dc:identifier id="BookID">urn:uuid:12345678-1234-1234-1234-123456789abc</dc:identifier>\n'
                '  </metadata>\n'
                '  <manifest>\n'
                '    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>\n'
                '    <item id="style" href="styles.css" media-type="text/css"/>\n'
                '    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>\n'
                '  </manifest>\n'
                '  <spine toc="ncx">\n'
                '    <itemref idref="chapter1"/>\n'
                '  </spine>\n'
                '</package>'
            )
            zip_file.writestr("OEBPS/content.opf", content_opf)

            # 2f. OEBPS/toc.ncx
            toc_ncx = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<!DOCTYPE ncx PUBLIC "-//NISO//DTD NCX 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">\n'
                '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
                '  <head>\n'
                '    <meta name="dtb:uid" content="urn:uuid:12345678-1234-1234-1234-123456789abc"/>\n'
                '  </head>\n'
                f'  <docTitle><text>{title}</text></docTitle>\n'
                '  <navMap>\n'
                '    <navPoint id="navpoint-1" playOrder="1">\n'
                f'      <navLabel><text>{title}</text></navLabel>\n'
                '      <content src="chapter1.xhtml"/>\n'
                '    </navPoint>\n'
                '  </navMap>\n'
                '</ncx>'
            )
            zip_file.writestr("OEBPS/toc.ncx", toc_ncx)

        epub_bytes = zip_buffer.getvalue()

        output_path = None
        if opts.destination == OutputDestination.FILE_PATH and opts.output_path:
            output_path = opts.output_path
            with open(output_path, "wb") as f:
                f.write(epub_bytes)

        return ExportResult(
            format_id=self.format_id,
            destination=opts.destination,
            content=epub_bytes,
            output_path=output_path,
        )
