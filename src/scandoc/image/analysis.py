"""
Lightweight document image analyzer evaluating resolution, brightness, contrast, blur, noise, and skew.
"""

import io
from pathlib import Path
from typing import BinaryIO, Optional, Union
import numpy as np
from PIL import Image, ImageOps
from pydantic import BaseModel, Field

from scandoc.image.exceptions import ImageAnalysisError, InvalidImageInputError


class ImageAnalysis(BaseModel):
    """
    Lightweight image quality and characteristic analysis summary.
    """
    width: int = Field(..., ge=1, description="Pixel width of image")
    height: int = Field(..., ge=1, description="Pixel height of image")
    aspect_ratio: float = Field(..., ge=0.0, description="Aspect ratio (width / height)")
    color_mode: str = Field(..., description="PIL color mode string ('RGB', 'L', '1', 'RGBA')")
    dpi: Optional[float] = Field(None, ge=1.0, description="DPI resolution if present in metadata")
    mean_brightness: float = Field(..., ge=0.0, le=255.0, description="Average pixel intensity (0=black, 255=white)")
    contrast_std: float = Field(..., ge=0.0, description="Pixel intensity standard deviation")
    blur_score: float = Field(..., ge=0.0, description="Laplacian variance sharpness score (higher = sharper)")
    noise_estimate: float = Field(..., ge=0.0, description="High-frequency noise variance estimate")
    skew_angle_deg: float = Field(0.0, ge=-45.0, le=45.0, description="Estimated text skew angle in degrees")
    is_low_res: bool = Field(False, description="True if image width/height < 1000px or DPI < 150")
    is_blurry: bool = Field(False, description="True if blur score < 80.0")
    is_low_contrast: bool = Field(False, description="True if contrast_std < 35.0")
    is_noisy: bool = Field(False, description="True if noise estimate > 25.0")
    is_skewed: bool = Field(False, description="True if abs(skew_angle_deg) > 0.5")


class ImageAnalyzer:
    """
    Fast, deterministic image analysis engine.
    """

    @classmethod
    def analyze(
        cls, image_input: Union[str, Path, bytes, bytearray, BinaryIO]
    ) -> ImageAnalysis:
        """
        Analyze image properties, quality metrics, and skew.
        
        Args:
            image_input: File path, bytes buffer, or binary stream.
            
        Returns:
            ImageAnalysis object.
        """
        img, raw_bytes = cls._load_pil_image(image_input)
        width, height = img.size
        aspect_ratio = round(width / max(1, height), 3)
        color_mode = img.mode

        # Extract DPI if available in metadata
        dpi_val: Optional[float] = None
        info_dpi = img.info.get("dpi")
        if info_dpi and isinstance(info_dpi, tuple) and len(info_dpi) >= 1:
            dpi_val = float(info_dpi[0])

        # Convert to Grayscale numpy array for fast numeric analysis
        gray_img = img.convert("L")
        arr = np.asarray(gray_img, dtype=np.float32)

        mean_brightness = float(np.mean(arr))
        contrast_std = float(np.std(arr))

        # Sharpness score via discrete Laplacian variance
        blur_score = cls._compute_blur_score(arr)

        # Noise score via high-pass spatial difference variance
        noise_estimate = cls._compute_noise_score(arr)

        # Skew angle estimation using Radon / projection variance
        skew_angle = cls._estimate_skew_angle(arr)

        is_low_res = width < 1000 or height < 1000 or (dpi_val is not None and dpi_val < 150)
        is_blurry = blur_score < 80.0
        is_low_contrast = contrast_std < 35.0
        is_noisy = noise_estimate > 25.0
        is_skewed = abs(skew_angle) > 0.5

        return ImageAnalysis(
            width=width,
            height=height,
            aspect_ratio=aspect_ratio,
            color_mode=color_mode,
            dpi=dpi_val,
            mean_brightness=round(mean_brightness, 2),
            contrast_std=round(contrast_std, 2),
            blur_score=round(blur_score, 2),
            noise_estimate=round(noise_estimate, 2),
            skew_angle_deg=round(skew_angle, 2),
            is_low_res=is_low_res,
            is_blurry=is_blurry,
            is_low_contrast=is_low_contrast,
            is_noisy=is_noisy,
            is_skewed=is_skewed,
        )

    @classmethod
    def _load_pil_image(
        cls, image_input: Union[str, Path, bytes, bytearray, BinaryIO]
    ) -> tuple[Image.Image, bytes]:
        """Load and validate PIL image."""
        try:
            if isinstance(image_input, (str, Path)):
                p = Path(image_input)
                if not p.exists():
                    raise InvalidImageInputError(f"Image file not found: {image_input}")
                raw_bytes = p.read_bytes()
            elif isinstance(image_input, (bytes, bytearray)):
                raw_bytes = bytes(image_input)
            elif hasattr(image_input, "read"):
                raw_bytes = image_input.read()
            else:
                raise InvalidImageInputError(f"Unsupported image input type: {type(image_input)}")

            if len(raw_bytes) == 0:
                raise InvalidImageInputError("Input image source is 0 bytes")

            img = Image.open(io.BytesIO(raw_bytes))
            img.load()
            return img, raw_bytes
        except InvalidImageInputError:
            raise
        except Exception as e:
            raise InvalidImageInputError(f"Failed to load or parse image: {e}") from e

    @staticmethod
    def _compute_blur_score(arr: np.ndarray) -> float:
        """Compute discrete 2D Laplacian variance."""
        if arr.shape[0] < 3 or arr.shape[1] < 3:
            return 100.0
        # 3x3 Discrete Laplacian kernel
        lap = (
            4 * arr[1:-1, 1:-1]
            - arr[:-2, 1:-1]
            - arr[2:, 1:-1]
            - arr[1:-1, :-2]
            - arr[1:-1, 2:]
        )
        return float(np.var(lap))

    @staticmethod
    def _compute_noise_score(arr: np.ndarray) -> float:
        """Compute high-frequency noise estimate using spatial neighbor differences."""
        if arr.shape[0] < 2 or arr.shape[1] < 2:
            return 0.0
        diff_x = np.abs(arr[:, 1:] - arr[:, :-1])
        diff_y = np.abs(arr[1:, :] - arr[:-1, :])
        return float((np.var(diff_x) + np.var(diff_y)) / 2.0)

    @staticmethod
    def _estimate_skew_angle(arr: np.ndarray) -> float:
        """
        Estimate text line skew angle (-15 to +15 deg) using projection profile variance.
        """
        if arr.shape[0] < 20 or arr.shape[1] < 20:
            return 0.0

        # Subsample image for speed
        step_y = max(1, arr.shape[0] // 300)
        step_x = max(1, arr.shape[1] // 300)
        sub_arr = arr[::step_y, ::step_x]

        # Binarize threshold
        bin_arr = (sub_arr < 180).astype(np.float32)
        if np.sum(bin_arr) == 0:
            return 0.0

        best_angle = 0.0
        max_var = -1.0

        # Sweep candidate angles in [-10, 10] range
        for angle in np.linspace(-10.0, 10.0, num=21):
            # Compute projection profile sum along rotated axis
            rad = np.radians(angle)
            cos_a, sin_a = np.cos(rad), np.sin(rad)
            h, w = bin_arr.shape
            cy, cx = h / 2.0, w / 2.0

            y_indices, x_indices = np.indices((h, w))
            y_rot = (y_indices - cy) * cos_a - (x_indices - cx) * sin_a + cy
            y_bin = np.clip(y_rot.astype(int), 0, h - 1)

            profile = np.bincount(y_bin.ravel(), weights=bin_arr.ravel(), minlength=h)
            var = float(np.var(profile))
            if var > max_var:
                max_var = var
                best_angle = float(angle)

        return best_angle
