"""
Try-On Generation Agent for AI Virtual Photographer.

This agent orchestrates the complete try-on image generation pipeline:
1. Analyzes the garment (via Garment Understanding Agent)
2. Builds the generation prompt (via Prompt Builder Agent)
3. Generates the try-on image (via Gemini image model)

This is the main "rendering camera" of the system.
"""

from typing import Optional, Tuple

from schemas.garment_schema import GarmentDescription
from schemas.generation_request import ModelPreferences, GenerationResponse
from agents.garment_understanding_agent import analyze_garment
from agents.prompt_builder_agent import build_image_prompt, build_simple_prompt
from services.gemini_client import get_gemini_client, GeminiClientError
from utils.logging_utils import get_agent_logger
from utils.image_utils import validate_image, image_to_base64

logger = get_agent_logger("TryOnGeneration")


def generate_tryon_image(
    garment_image_bytes: bytes,
    preferences: Optional[ModelPreferences] = None,
    cached_description: Optional[GarmentDescription] = None
) -> Tuple[bytes, GarmentDescription, str]:
    """
    Generate a try-on image showing a model wearing the garment.
    
    This is the main entry point for the Try-On Generation Agent.
    It orchestrates the complete pipeline from garment analysis
    to final image generation.
    
    Args:
        garment_image_bytes: Original garment image bytes
        preferences: User preferences for the generated image
        cached_description: Previously analyzed garment description (optional)
    
    Returns:
        Tuple of (generated_image_bytes, garment_description, prompt_used)
    
    Raises:
        ValueError: If garment image is invalid
        GeminiClientError: If any API call fails
    
    Example:
        >>> with open("kurta.jpg", "rb") as f:
        ...     garment_bytes = f.read()
        >>> image_bytes, description, prompt = generate_tryon_image(garment_bytes)
        >>> with open("tryon_result.png", "wb") as f:
        ...     f.write(image_bytes)
    """
    logger.info("Starting try-on image generation pipeline...")
    
    # Step 1: Validate input image
    is_valid, message = validate_image(garment_image_bytes)
    if not is_valid:
        logger.error(f"Invalid garment image: {message}")
        raise ValueError(f"Invalid garment image: {message}")
    logger.info(f"Input image validated: {message}")
    
    # Step 2: Analyze garment (or use cached)
    if cached_description:
        logger.info("Using cached garment description")
        description = cached_description
    else:
        logger.info("Analyzing garment image...")
        description = analyze_garment(garment_image_bytes)
        logger.info(f"Garment analysis complete: {description.get_summary()}")
    
    # Step 3: Build generation prompt
    logger.info("Building image generation prompt...")
    if preferences is None:
        preferences = ModelPreferences()
    
    prompt = build_image_prompt(description, preferences)
    logger.info(f"Prompt built ({len(prompt)} characters)")
    
    # Step 4: Generate image
    logger.info("Calling image generation API...")
    try:
        client = get_gemini_client()
        generated_bytes = client.generate_image(
            prompt=prompt,
            reference_image_bytes=garment_image_bytes
        )
        logger.info("Try-on image generated successfully!")
        return generated_bytes, description, prompt
        
    except GeminiClientError as e:
        logger.warning(f"Generation failed with detailed prompt, trying simpler prompt: {e}")
        
        # Try with simpler prompt
        simple_prompt = build_simple_prompt(
            description,
            gender="male" if "male" in description.gender_usage else "female"
        )
        
        try:
            generated_bytes = client.generate_image(prompt=simple_prompt)
            logger.info("Try-on image generated with simplified prompt")
            return generated_bytes, description, simple_prompt
        except GeminiClientError as e2:
            logger.error(f"Image generation failed completely: {e2}")
            raise


def generate_tryon_response(
    garment_image_bytes: bytes,
    preferences: Optional[ModelPreferences] = None,
    cached_description: Optional[GarmentDescription] = None
) -> GenerationResponse:
    """
    Generate try-on image and return a structured response.
    
    This is a convenience wrapper that returns a GenerationResponse
    object suitable for API responses.
    
    Args:
        garment_image_bytes: Original garment image bytes
        preferences: User preferences for the generated image
        cached_description: Previously analyzed garment description
    
    Returns:
        GenerationResponse with success status and results
    """
    try:
        image_bytes, description, prompt = generate_tryon_image(
            garment_image_bytes,
            preferences,
            cached_description
        )
        
        return GenerationResponse(
            success=True,
            generated_image_base64=image_to_base64(image_bytes),
            prompt_used=prompt,
            garment_description=description
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return GenerationResponse(
            success=False,
            error=f"Invalid input: {str(e)}"
        )
        
    except GeminiClientError as e:
        logger.error(f"API error: {e}")
        return GenerationResponse(
            success=False,
            error=f"Generation failed: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return GenerationResponse(
            success=False,
            error=f"Unexpected error: {str(e)}"
        )


def batch_generate(
    garment_image_bytes_list: list[bytes],
    preferences: Optional[ModelPreferences] = None
) -> list[GenerationResponse]:
    """
    Generate try-on images for multiple garments.
    
    Args:
        garment_image_bytes_list: List of garment image bytes
        preferences: Shared preferences for all generations
    
    Returns:
        List of GenerationResponse objects
    """
    logger.info(f"Starting batch generation for {len(garment_image_bytes_list)} images...")
    
    results = []
    for i, image_bytes in enumerate(garment_image_bytes_list):
        logger.info(f"Processing image {i + 1}/{len(garment_image_bytes_list)}...")
        response = generate_tryon_response(image_bytes, preferences)
        results.append(response)
    
    success_count = sum(1 for r in results if r.success)
    logger.info(f"Batch complete: {success_count}/{len(results)} successful")
    
    return results
