import re
path = "src/scandoc/agent/routing.py"
with open(path, "r") as f:
    content = f.read()

# Add imports if missing
if "from scandoc.providers.layout.rtdetr_provider import RtDetrLayoutProvider" not in content:
    content = content.replace(
        "from scandoc.providers.vlm import LocalVlmProvider, VlmRequest, VlmTaskType",
        "from scandoc.providers.vlm import LocalVlmProvider, VlmRequest, VlmTaskType\nfrom scandoc.providers.layout.rtdetr_provider import RtDetrLayoutProvider\nfrom scandoc.models.blocks import FigureBlock, ImageRef\nimport base64\nfrom PIL import Image\nimport io\nimport pypdfium2 as pdfium"
    )

# Add init provider
if "self._layout_provider: Optional[RtDetrLayoutProvider] = None" not in content:
    content = content.replace(
        "self._vlm_provider: Optional[LocalVlmProvider] = None",
        "self._vlm_provider: Optional[LocalVlmProvider] = None\n        self._layout_provider: Optional[RtDetrLayoutProvider] = None"
    )

# Modify _execute_deep_path
deep_path_code = """    def _execute_deep_path(
        self, source: Union[str, Path, bytes], file_name: Optional[str], cls_res: ClassificationResult
    ) -> Tuple[DocumentIR, List[DecisionTrace]]:
        \"\"\"Deep ML Layout & OCR Processing for scanned PDFs and complex multi-column documents.\"\"\"
        doc_ir = self.ingestor.ingest(source, file_name=file_name)
        traces = []
        
        if self._layout_provider is None:
            self._layout_provider = RtDetrLayoutProvider()

        # Reopen PDF to render images for the layout provider
        try:
            pdf = pdfium.PdfDocument(source)
            for page in doc_ir.pages:
                p_score = next((p for p in cls_res.pages if p.page_index == page.page_index), None)
                comp = p_score.complexity_score if p_score else 0.5
                
                try:
                    pdf_page = pdf[page.page_index]
                    pil_img = pdf_page.render(scale=2.0).to_pil()
                    buf = io.BytesIO()
                    pil_img.save(buf, format="PNG")
                    
                    layout_res = self._layout_provider.detect_layout(buf.getvalue(), page_index=page.page_index)
                    for reg in layout_res.regions:
                        if reg.category.name == "FIGURE":
                            # Crop figure from PIL image
                            l = int(reg.bbox.l * pil_img.width)
                            t = int(reg.bbox.t * pil_img.height)
                            r = int(reg.bbox.r * pil_img.width)
                            b = int(reg.bbox.b * pil_img.height)
                            cropped = pil_img.crop((l, t, r, b))
                            
                            cbuf = io.BytesIO()
                            cropped.save(cbuf, format="PNG")
                            b64 = base64.b64encode(cbuf.getvalue()).decode("utf-8")
                            
                            fig_block = FigureBlock(
                                id=f"fig_ml_{page.page_index}_{reg.region_idx}",
                                bbox=reg.bbox,
                                image_ref=ImageRef(
                                    mime_type="image/png",
                                    width_px=cropped.width,
                                    height_px=cropped.height,
                                    base64_data=b64
                                )
                            )
                            page.blocks.append(fig_block)
                except Exception as e:
                    logger.warning(f"Failed ML layout extraction on page {page.page_index}: {e}")

                # Still order the blocks using XY Cut
                layout_analyzer_res = LayoutAnalyzer.analyze_page(page, page_width=page.width, page_height=page.height)
                page.blocks = layout_analyzer_res.ordered_blocks

                traces.append(
                    DecisionTrace(
                        page_index=page.page_index,
                        decision="DEEP_ML_LAYOUT_AND_OCR",
                        reason=f"Scanned/complex page (complexity: {comp}). Escalated to RT-DETR layout.",
                        provider_id="rtdetr_layout",
                        mode="LOCAL",
                    )
                )
        finally:
            if 'pdf' in locals():
                pdf.close()

        return doc_ir, traces"""

content = re.sub(r'    def _execute_deep_path\(.*?return doc_ir, traces', deep_path_code, content, flags=re.DOTALL)

with open(path, "w") as f:
    f.write(content)
