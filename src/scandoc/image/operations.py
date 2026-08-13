"""
Modular image preprocessing operations for OCR image enhancement.
"""

from abc import ABC, abstractmethod
import math
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from scandoc.image.exceptions import PreprocessingError


class BaseImageOp(ABC):
    """
    Abstract Base Class for individual image preprocessing operations.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return unique operation identifier."""
        pass

    @abstractmethod
    def apply(self, image: Image.Image) -> Image.Image:
        """
        Apply operation to PIL image and return processed PIL image copy.
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"


class GrayscaleOp(BaseImageOp):
    """Convert RGB/RGBA image to 8-bit grayscale ('L')."""

    @property
    def name(self) -> str:
        return "grayscale"

    def apply(self, image: Image.Image) -> Image.Image:
        if image.mode == "L":
            return image.copy()
        return image.convert("L")


class ResizeDpiOp(BaseImageOp):
    """Resize image to achieve target DPI or minimum dimension."""

    def __init__(self, target_dpi: int = 300, min_width: int = 1200):
        self.target_dpi = target_dpi
        self.min_width = min_width

    @property
    def name(self) -> str:
        return f"resize_dpi_{self.target_dpi}"

    def apply(self, image: Image.Image) -> Image.Image:
        w, h = image.size
        if w >= self.min_width:
            return image.copy()

        scale = self.min_width / max(1, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        return image.resize((new_w, new_h), Image.Resampling.LANCZOS)


class ContrastBrightnessOp(BaseImageOp):
    """Adjust contrast and brightness ratios."""

    def __init__(self, contrast_factor: float = 1.3, brightness_factor: float = 1.05):
        self.contrast_factor = contrast_factor
        self.brightness_factor = brightness_factor

    @property
    def name(self) -> str:
        return f"contrast_{self.contrast_factor}_brightness_{self.brightness_factor}"

    def apply(self, image: Image.Image) -> Image.Image:
        out = image.copy()
        if self.contrast_factor != 1.0:
            enhancer = ImageEnhance.Contrast(out)
            out = enhancer.enhance(self.contrast_factor)
        if self.brightness_factor != 1.0:
            enhancer = ImageEnhance.Brightness(out)
            out = enhancer.enhance(self.brightness_factor)
        return out


class DenoiseOp(BaseImageOp):
    """Apply median spatial filtering to reduce high-frequency noise."""

    def __init__(self, size: int = 3):
        self.size = size

    @property
    def name(self) -> str:
        return f"denoise_median_{self.size}"

    def apply(self, image: Image.Image) -> Image.Image:
        return image.filter(ImageFilter.MedianFilter(size=self.size))


class SharpenOp(BaseImageOp):
    """Apply spatial sharpening filter."""

    @property
    def name(self) -> str:
        return "sharpen"

    def apply(self, image: Image.Image) -> Image.Image:
        return image.filter(ImageFilter.SHARPEN)


class AdaptiveThresholdOp(BaseImageOp):
    """Apply adaptive binarization thresholding for document text extraction."""

    def __init__(self, block_size: int = 15, C: int = 10):
        self.block_size = block_size
        self.C = C

    @property
    def name(self) -> str:
        return f"adaptive_threshold_{self.block_size}"

    def apply(self, image: Image.Image) -> Image.Image:
        gray = image.convert("L")
        arr = np.asarray(gray, dtype=np.float32)

        # Fast local spatial mean via BoxBlur
        radius = max(1, self.block_size // 2)
        mean_img = gray.filter(ImageFilter.BoxBlur(radius=radius))
        mean_arr = np.asarray(mean_img, dtype=np.float32)

        binary_arr = np.where(arr < (mean_arr - self.C), 0, 255).astype(np.uint8)
        return Image.fromarray(binary_arr)


class RotateOp(BaseImageOp):
    """Rotate image by explicit angle in degrees (90, 180, 270)."""

    def __init__(self, angle_deg: float):
        self.angle_deg = angle_deg

    @property
    def name(self) -> str:
        return f"rotate_{self.angle_deg}"

    def apply(self, image: Image.Image) -> Image.Image:
        if self.angle_deg == 0:
            return image.copy()
        return image.rotate(self.angle_deg, expand=True, resample=Image.Resampling.BICUBIC)


class DeskewOp(BaseImageOp):
    """Rotate image to correct estimated skew angle."""

    def __init__(self, angle_deg: float):
        self.angle_deg = angle_deg

    @property
    def name(self) -> str:
        return f"deskew_{self.angle_deg:.1f}deg"

    def apply(self, image: Image.Image) -> Image.Image:
        if abs(self.angle_deg) < 0.2:
            return image.copy()
        # Rotate opposite to skew angle
        return image.rotate(-self.angle_deg, expand=True, fillcolor=(255, 255, 255))


class CropBorderOp(BaseImageOp):
    """Crop solid margin borders around document edges."""

    def __init__(self, margin_px: int = 10):
        self.margin_px = margin_px

    @property
    def name(self) -> str:
        return f"crop_border_m{self.margin_px}"

    def apply(self, image: Image.Image) -> Image.Image:
        w, h = image.size
        if w <= self.margin_px * 2 or h <= self.margin_px * 2:
            return image.copy()
        return image.crop((self.margin_px, self.margin_px, w - self.margin_px, h - self.margin_px))
