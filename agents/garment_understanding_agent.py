"""
Garment Understanding Agent for AI Virtual Photographer.

This agent is the "understanding brain" of the system. It analyzes
garment images using Gemini's vision capabilities and extracts
structured information about the garment.

The agent is designed as an Indian ethnic fashion expert.
"""

import json
import re
from typing import Optional

from schemas.garment_schema import GarmentDescription
from services.gemini_client import get_gemini_client, GeminiClientError
from utils.logging_utils import get_agent_logger
from utils.image_utils import validate_image, resize_if_needed

logger = get_agent_logger("GarmentUnderstanding")


# System prompt that sets up the model as an Indian ethnic fashion expert
SYSTEM_PROMPT = """You are an expert in Indian ethnic fashion with deep knowledge of:
- Traditional garments: kurta, sherwani, lehenga, saree, anarkali, salwar kameez, etc.
- Regional styles: North Indian, South Indian, Gujarati, Rajasthani, Punjabi, Bengali, etc.
- Fabric types: silk, cotton, chiffon, georgette, velvet, brocade, khadi, etc.
- Embroidery techniques: zari, zardozi, phulkari, chikankari, mirror work, gota patti, etc.
- Pattern styles: paisley, floral, geometric, ikat, bandhani, block print, etc.

Your task is to analyze garment images and extract detailed structured information.

IMPORTANT RULES:
1. Be accurate - only describe what you can clearly see in the image
2. If a detail is not visible or unclear, use null or empty list
3. Do NOT hallucinate or guess details that aren't visible
4. Focus on preserving details needed for accurate recreation
5. Pay special attention to embroidery patterns, colors, and placement
6. Note any unique or distinctive features of the garment"""


def _get_user_prompt() -> str:
    """Generate the user prompt with schema instructions."""
    return """Analyze this garment image and return a JSON object with the following structure.
Return ONLY valid JSON, no other text or markdown.

{
    "garment_type": "string or null - e.g. kurta, sherwani, lehenga, anarkali, saree",
    "gender_usage": ["male", "female", or "unisex"],
    "region_inspiration": ["list of regional styles if identifiable"],
    "occasion": ["wedding", "festive", "casual", "formal", etc.],
    "silhouette": {
        "length": "knee-length, ankle-length, floor-length, etc.",
        "fit": "straight, A-line, flared, fitted, etc.",
        "sleeve": "full-sleeve, half-sleeve, sleeveless, etc.",
        "neckline": "bandhgala, V-neck, round, mandarin, etc."
    },
    "fabrics": [
        {
            "name": "silk, cotton, chiffon, etc.",
            "approx_weight": "light, medium, heavy",
            "sheen": "high, medium, matte"
        }
    ],
    "colors": {
        "primary": "main color with shade description",
        "secondary": ["list of secondary colors"],
        "pattern_colors": ["colors used in patterns/embroidery"]
    },
    "embroidery": [
        {
            "style": "zari, zardozi, chikankari, mirror work, etc.",
            "motifs": ["circular floral", "paisley", "geometric", etc.],
            "density": "heavy, medium, sparse",
            "placement": ["front panel", "cuffs", "collar", "hem", "border"]
        }
    ],
    "patterns": [
        {
            "name": "geometric, floral, paisley, abstract, etc.",
            "shapes": ["specific shapes in pattern"],
            "layout": "all-over, border, central motif, scattered",
            "scale": "small, medium, large"
        }
    ],
    "draping": {
        "has_dupatta": true or false or null,
        "layering": "single-layer, two-piece, description of layers",
        "hem_style": "straight, rounded, asymmetric, etc."
    },
    "styling_notes": ["indo-western", "traditional", "royal", "minimalist", etc.],
    "free_text_description": "A detailed paragraph describing the garment's unique features, overall aesthetic, and any details not captured above"
}

Analyze the image carefully and fill in as many fields as possible. Use null for single values and [] for lists when information is not visible."""


def _extract_json_from_response(response_text: str) -> dict:
    """
    Extract JSON from model response, handling markdown code blocks.
    
    Args:
        response_text: Raw response text from the model
    
    Returns:
        Parsed JSON dictionary
    
    Raises:
        ValueError: If JSON cannot be extracted
    """
    # Try direct JSON parse first
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract from markdown code block
    json_patterns = [
        r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
        r'```\s*([\s\S]*?)\s*```',       # ``` ... ```
        r'\{[\s\S]*\}',                  # Raw JSON object
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, response_text)
        if match:
            try:
                json_str = match.group(1) if '```' in pattern else match.group(0)
                return json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                continue
    
    raise ValueError(f"Could not extract JSON from response: {response_text[:500]}...")


def analyze_garment(image_bytes: bytes) -> GarmentDescription:
    """
    Analyze a garment image and extract structured description.
    
    This is the main entry point for the Garment Understanding Agent.
    It takes an image of a garment (flat-lay, mannequin, or catalog shot)
    and returns a structured GarmentDescription.
    
    Args:
        image_bytes: Raw image data (JPEG, PNG, or WEBP)
    
    Returns:
        GarmentDescription with extracted garment details
    
    Raises:
        ValueError: If image is invalid
        GeminiClientError: If API call fails
    
    Example:
        >>> with open("kurta.jpg", "rb") as f:
        ...     image_bytes = f.read()
        >>> description = analyze_garment(image_bytes)
        >>> print(description.garment_type)
        "kurta"
        >>> print(description.colors.primary)
        "deep maroon"
    """
    logger.info("Starting garment analysis...")
    
    # Step 1: Validate image
    is_valid, message = validate_image(image_bytes)
    if not is_valid:
        logger.error(f"Image validation failed: {message}")
        raise ValueError(message)
    logger.info(f"Image validated: {message}")
    
    # Step 2: Resize if needed
    image_bytes = resize_if_needed(image_bytes)
    
    # Step 3: Call Gemini API
    try:
        client = get_gemini_client()
        response_text = client.analyze_image(
            image_bytes=image_bytes,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=_get_user_prompt()
        )
        logger.debug(f"Raw API response: {response_text[:500]}...")
    except GeminiClientError as e:
        logger.error(f"Gemini API call failed: {e}")
        raise
    
    # Step 4: Parse JSON response
    try:
        garment_json = _extract_json_from_response(response_text)
        logger.info("Successfully extracted JSON from response")
    except ValueError as e:
        logger.error(f"JSON extraction failed: {e}")
        # Return a minimal description with the free text
        return GarmentDescription(
            free_text_description=f"Analysis incomplete. Raw response: {response_text[:1000]}"
        )
    
    # Step 5: Validate and create GarmentDescription
    try:
        description = GarmentDescription.model_validate(garment_json)
        logger.info(f"Garment analysis complete: {description.get_summary()}")
        return description
    except Exception as e:
        logger.warning(f"Schema validation warning: {e}")
        # Try to create with available fields
        return GarmentDescription(**{k: v for k, v in garment_json.items() 
                                     if k in GarmentDescription.model_fields})


def analyze_garment_with_retry(
    image_bytes: bytes,
    max_retries: int = 2
) -> Optional[GarmentDescription]:
    """
    Analyze garment with simplified retry on failure.
    
    If the detailed analysis fails, attempts a simpler prompt.
    
    Args:
        image_bytes: Raw image data
        max_retries: Maximum retry attempts
    
    Returns:
        GarmentDescription or None if all attempts fail
    """
    for attempt in range(max_retries + 1):
        try:
            return analyze_garment(image_bytes)
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries:
                logger.error("All analysis attempts failed")
                return None
    
    return None
