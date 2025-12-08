"""
Image utilities for AI Virtual Photographer.

Handles image validation, format conversion, and preprocessing
for Gemini API calls.
"""

import base64
import io
from typing import Tuple, Optional
from PIL import Image

from utils.logging_utils import setup_logger

logger = setup_logger(__name__)


# Supported image formats
SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# Maximum dimensions for API calls
MAX_DIMENSION = 4096  # Gemini's max supported dimension


def validate_image(image_bytes: bytes) -> Tuple[bool, str]:
    """
    Validate that the provided bytes represent a valid image.
    
    Args:
        image_bytes: Raw image data
    
    Returns:
        Tuple of (is_valid, message)
    
    Example:
        >>> with open("garment.jpg", "rb") as f:
        ...     is_valid, msg = validate_image(f.read())
        >>> print(msg)
        "Valid JPEG image (800x1200)"
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()  # Verify it's actually an image
        
        # Reopen after verify (verify() can only be called once)
        image = Image.open(io.BytesIO(image_bytes))
        
        if image.format not in SUPPORTED_FORMATS:
            return False, f"Unsupported format: {image.format}. Use JPEG, PNG, or WEBP."
        
        width, height = image.size
        return True, f"Valid {image.format} image ({width}x{height})"
        
    except Exception as e:
        logger.error(f"Image validation failed: {e}")
        return False, f"Invalid image: {str(e)}"


def resize_if_needed(
    image_bytes: bytes,
    max_dimension: int = MAX_DIMENSION
) -> bytes:
    """
    Resize image if it exceeds maximum dimensions.
    
    Maintains aspect ratio while ensuring neither dimension
    exceeds the maximum.
    
    Args:
        image_bytes: Raw image data
        max_dimension: Maximum allowed width or height
    
    Returns:
        Resized image bytes (or original if no resize needed)
    """
    image = Image.open(io.BytesIO(image_bytes))
    width, height = image.size
    
    # Check if resize is needed
    if width <= max_dimension and height <= max_dimension:
        logger.debug(f"Image size {width}x{height} is within limits")
        return image_bytes
    
    # Calculate new dimensions maintaining aspect ratio
    ratio = min(max_dimension / width, max_dimension / height)
    new_width = int(width * ratio)
    new_height = int(height * ratio)
    
    logger.info(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
    
    # Resize with high-quality resampling
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Convert back to bytes
    output = io.BytesIO()
    resized.save(output, format=image.format or "JPEG", quality=95)
    return output.getvalue()


def image_to_base64(image_bytes: bytes) -> str:
    """
    Convert image bytes to base64 string.
    
    Args:
        image_bytes: Raw image data
    
    Returns:
        Base64 encoded string
    """
    return base64.b64encode(image_bytes).decode("utf-8")


def base64_to_image(base64_string: str) -> bytes:
    """
    Convert base64 string back to image bytes.
    
    Args:
        base64_string: Base64 encoded image
    
    Returns:
        Raw image bytes
    """
    return base64.b64decode(base64_string)


def get_image_format(image_bytes: bytes) -> Optional[str]:
    """
    Detect the format of an image from its bytes.
    
    Args:
        image_bytes: Raw image data
    
    Returns:
        Format string (e.g., "JPEG", "PNG") or None if unknown
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return image.format
    except Exception:
        return None


def get_mime_type(image_bytes: bytes) -> str:
    """
    Get the MIME type for an image.
    
    Args:
        image_bytes: Raw image data
    
    Returns:
        MIME type string (e.g., "image/jpeg")
    """
    format_map = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
        "GIF": "image/gif",
    }
    
    img_format = get_image_format(image_bytes)
    return format_map.get(img_format, "image/jpeg")


def convert_to_rgb(image_bytes: bytes) -> bytes:
    """
    Ensure image is in RGB mode (required for some operations).
    
    Converts RGBA, P (palette), or other modes to RGB.
    
    Args:
        image_bytes: Raw image data
    
    Returns:
        Image bytes in RGB mode
    """
    image = Image.open(io.BytesIO(image_bytes))
    
    if image.mode == "RGB":
        return image_bytes
    
    logger.info(f"Converting image from {image.mode} to RGB")
    
    # Handle transparency by compositing on white background
    if image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
        image = background
    else:
        image = image.convert("RGB")
    
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=95)
    return output.getvalue()
