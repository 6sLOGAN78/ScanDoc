"""
AssetResolver resolving image assets to embedded base64 URLs or file system references.
"""

import base64
from pathlib import Path
from typing import Optional, Tuple

from scandoc.exporters.models import ExportOptions
from scandoc.exporters.taxonomy import ImageHandlingStrategy


class AssetResolver:
    """
    Common asset resolution helper for all exporters.
    """

    @classmethod
    def resolve_image_asset(
        cls,
        image_bytes: Optional[bytes],
        asset_id: str,
        options: ExportOptions,
        mime_type: str = "image/png",
    ) -> Tuple[str, Optional[str]]:
        """
        Resolve image bytes into a URI (base64 or file path) and return (src_uri, warning_or_asset_path).
        """
        if not image_bytes:
            return f"[Missing Image Asset: {asset_id}]", f"Image asset '{asset_id}' has no binary content."

        if options.image_strategy == ImageHandlingStrategy.EMBED_BASE64:
            b64_str = base64.b64encode(image_bytes).decode("ascii")
            src = f"data:{mime_type};base64,{b64_str}"
            return src, None

        elif options.image_strategy == ImageHandlingStrategy.FILE_REFERENCE:
            asset_dir = Path(options.asset_dir) if options.asset_dir else Path("assets")
            asset_dir.mkdir(parents=True, exist_ok=True)
            ext = ".png" if "png" in mime_type else ".jpg"
            file_name = f"{asset_id}{ext}"
            target_path = asset_dir / file_name
            target_path.write_bytes(image_bytes)
            return str(target_path), str(target_path)

        return f"[Unsupported Strategy: {options.image_strategy}]", "Unsupported image handling strategy."
