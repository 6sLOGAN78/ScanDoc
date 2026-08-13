"""
Document hierarchy tree builder reconstructing section/subsection structure.
"""

import uuid
from typing import Dict, List, Optional

from scandoc.models import DocumentIR, Page
from scandoc.models.blocks import HeadingBlock, TextBlock
from scandoc.structure.models import (
    DocumentHierarchy,
    DocumentHierarchyNode,
    ReadingOrderResult,
)


class DocumentHierarchyBuilder:
    """
    Constructs hierarchical section tree nodes from document heading blocks.
    """

    @classmethod
    def build_hierarchy(
        cls,
        doc: DocumentIR,
        reading_orders: Optional[List[ReadingOrderResult]] = None,
    ) -> DocumentHierarchy:
        root_nodes: List[DocumentHierarchyNode] = []
        current_section: Optional[DocumentHierarchyNode] = None
        current_subsection: Optional[DocumentHierarchyNode] = None

        # Build reading map if provided
        reading_order_map: Dict[int, List[str]] = {}
        if reading_orders:
            for ro in reading_orders:
                reading_order_map[ro.page_index] = ro.ordered_block_ids

        for page in doc.pages:
            # Get blocks in reading sequence order if available
            ordered_ids = reading_order_map.get(page.page_index)
            if ordered_ids:
                block_lookup = {b.id: b for b in page.blocks}
                blocks = [block_lookup[bid] for bid in ordered_ids if bid in block_lookup]
            else:
                blocks = page.blocks

            for block in blocks:
                if isinstance(block, HeadingBlock):
                    node_id = f"section_{uuid.uuid4().hex[:8]}"
                    title_text = block.text or f"Section {len(root_nodes) + 1}"

                    if block.level == 1 or current_section is None:
                        current_section = DocumentHierarchyNode(
                            node_id=node_id,
                            title=title_text,
                            level=1,
                            block_ids=[block.id],
                            children=[],
                        )
                        root_nodes.append(current_section)
                        current_subsection = None
                    else:
                        current_subsection = DocumentHierarchyNode(
                            node_id=node_id,
                            title=title_text,
                            level=block.level,
                            block_ids=[block.id],
                            children=[],
                        )
                        current_section.children.append(current_subsection)

                else:
                    if current_subsection:
                        current_subsection.block_ids.append(block.id)
                    elif current_section:
                        current_section.block_ids.append(block.id)
                    else:
                        # Unclassified top-level block
                        if not root_nodes:
                            root_nodes.append(
                                DocumentHierarchyNode(
                                    node_id="section_root",
                                    title="Main Document",
                                    level=1,
                                    block_ids=[],
                                    children=[],
                                )
                            )
                        root_nodes[0].block_ids.append(block.id)

        return DocumentHierarchy(
            root_nodes=root_nodes,
            metadata={"num_sections": str(len(root_nodes))},
        )
