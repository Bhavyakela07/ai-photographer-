"""
Gemini API Client for AI Virtual Photographer.

This module provides a unified interface to Google's Gemini models:
- Gemini 2.0/3.0: Text + Vision (for garment understanding)
- Imagen 3 / Gemini native: Image Generation (for try-on rendering)

All Gemini API interactions are isolated here for easy maintenance
and model swapping.

Uses the new google-genai SDK with quality optimization.
"""

import time
import io
import base64
from typing import Optional, List
from google import genai
from google.genai import types

from config.settings import settings
from utils.logging_utils import get_service_logger
from utils.image_utils import get_mime_type

logger = get_service_logger("GeminiClient")


class GeminiClientError(Exception):
    """Custom exception for Gemini API errors."""
    pass


class GeminiClient:
    """
    Unified client for Gemini API interactions with quality optimization.
    
    This class wraps both the text+vision model (for analysis) and
    the image generation capabilities (for try-on rendering).
    
    Quality settings are loaded from config/settings.py and can be
    customized via environment variables.
    """
    
    def __init__(self):
        """Initialize the Gemini client with API key."""
        if not settings.GEMINI_API_KEY:
            raise GeminiClientError(
                "GEMINI_API_KEY not configured. Please set it in your .env file."
            )
        
        # Initialize the client with API key
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        logger.info(f"GeminiClient initialized")
        logger.info(f"  Text model: {settings.TEXT_VISION_MODEL_ID}")
        logger.info(f"  Image model: {settings.IMAGE_MODEL_ID}")
        logger.info(f"  Aspect ratio: {settings.IMAGE_ASPECT_RATIO}")
        logger.info(f"  Prompt enhancement: {settings.ENABLE_PROMPT_ENHANCEMENT}")
    
    def _enhance_prompt_for_quality(self, prompt: str) -> str:
        """
        Enhance the prompt with quality keywords for better image generation.
        
        Args:
            prompt: Original prompt
            
        Returns:
            Enhanced prompt with quality keywords
        """
        if not settings.AUTO_QUALITY_KEYWORDS:
            return prompt
        
        quality_keywords = settings.QUALITY_KEYWORDS
        
        # Add quality prefix and suffix
        enhanced = f"""Create a {quality_keywords} image.

{prompt}

Technical requirements:
- Ultra high resolution and sharp details
- Professional studio lighting
- Photorealistic quality
- Perfect color accuracy
- No artifacts or distortions"""
        
        logger.debug(f"Enhanced prompt with quality keywords")
        return enhanced
    
    def analyze_image(
        self,
        image_bytes: bytes,
        system_prompt: str,
        user_prompt: str,
        retry_count: int = 0
    ) -> str:
        """
        Analyze an image using Gemini text+vision model.
        
        Args:
            image_bytes: Raw image data
            system_prompt: System-level instructions
            user_prompt: User-level prompt with specific request
            retry_count: Current retry attempt (internal use)
        
        Returns:
            Raw response text from the model (expected to be JSON)
        
        Raises:
            GeminiClientError: If analysis fails after retries
        """
        logger.info("Analyzing image with Gemini text+vision model...")
        
        try:
            # Prepare image for the API
            mime_type = get_mime_type(image_bytes)
            
            # Create image part
            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )
            
            # Combine prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Generate response
            response = self._client.models.generate_content(
                model=settings.TEXT_VISION_MODEL_ID,
                contents=[full_prompt, image_part],
                config=types.GenerateContentConfig(
                    temperature=settings.ANALYSIS_TEMPERATURE,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=4096,
                )
            )
            
            # Extract text response
            if response.text:
                logger.info("Image analysis completed successfully")
                return response.text
            else:
                raise GeminiClientError("Empty response from model")
                
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            
            # Retry logic
            if retry_count < settings.MAX_RETRIES:
                wait_time = settings.RETRY_DELAY_SECONDS * (2 ** retry_count)
                logger.info(f"Retrying in {wait_time}s... (attempt {retry_count + 1}/{settings.MAX_RETRIES})")
                time.sleep(wait_time)
                return self.analyze_image(image_bytes, system_prompt, user_prompt, retry_count + 1)
            
            raise GeminiClientError(f"Image analysis failed after {settings.MAX_RETRIES} retries: {e}")
    
    def generate_image(
        self,
        prompt: str,
        reference_image_bytes: Optional[bytes] = None,
        retry_count: int = 0
    ) -> bytes:
        """
        Generate an image with quality optimization.
        
        Uses settings from config for:
        - Aspect ratio
        - Quality keywords
        - Prompt enhancement
        - Safety filters
        
        Args:
            prompt: Detailed text prompt describing the desired image
            reference_image_bytes: Optional reference image for style guidance
            retry_count: Current retry attempt (internal use)
        
        Returns:
            Generated image as bytes
        
        Raises:
            GeminiClientError: If generation fails after retries
        """
        logger.info("Generating high-quality image...")
        logger.info(f"  Model: {settings.IMAGE_MODEL_ID}")
        logger.info(f"  Aspect ratio: {settings.IMAGE_ASPECT_RATIO}")
        
        # Enhance prompt for quality
        enhanced_prompt = self._enhance_prompt_for_quality(prompt)
        logger.debug(f"Prompt length: {len(enhanced_prompt)} chars")
        
        try:
            # Try Imagen 3 first (highest quality)
            if "imagen" in settings.IMAGE_MODEL_ID.lower():
                return self._generate_with_imagen(enhanced_prompt, reference_image_bytes, retry_count)
            else:
                return self._generate_with_native(enhanced_prompt, reference_image_bytes, retry_count)
                
        except Exception as e:
            error_str = str(e)
            logger.error(f"Image generation failed: {error_str}")
            
            # Try native generation as fallback
            if "imagen" in settings.IMAGE_MODEL_ID.lower():
                logger.info("Falling back to native Gemini image generation...")
                try:
                    return self._generate_with_native(enhanced_prompt, reference_image_bytes, retry_count)
                except Exception as e2:
                    logger.error(f"Native fallback also failed: {e2}")
            
            # Retry logic
            if retry_count < settings.MAX_RETRIES:
                wait_time = settings.RETRY_DELAY_SECONDS * (2 ** retry_count)
                logger.info(f"Retrying in {wait_time}s... (attempt {retry_count + 1}/{settings.MAX_RETRIES})")
                time.sleep(wait_time)
                return self.generate_image(prompt, reference_image_bytes, retry_count + 1)
            
            raise GeminiClientError(f"Image generation failed after {settings.MAX_RETRIES} retries: {e}")
    
    def _generate_with_imagen(
        self,
        prompt: str,
        reference_image_bytes: Optional[bytes] = None,
        retry_count: int = 0
    ) -> bytes:
        """
        Generate image using Imagen 3 (highest quality).
        
        Imagen 3 generates at 1024px with options for upsampling.
        """
        logger.info(f"Using Imagen 3: {settings.IMAGE_MODEL_ID}")
        
        try:
            response = self._client.models.generate_images(
                model=settings.IMAGE_MODEL_ID,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=settings.IMAGE_COUNT,
                    aspect_ratio=settings.IMAGE_ASPECT_RATIO,
                    safety_filter_level=settings.SAFETY_FILTER_LEVEL,
                )
            )
            
            if response.generated_images:
                image_data = response.generated_images[0].image
                logger.info("✅ Image generated successfully with Imagen 3")
                
                # Get image bytes from the response
                if hasattr(image_data, 'image_bytes'):
                    return image_data.image_bytes
                elif hasattr(image_data, '_pil_image'):
                    buffer = io.BytesIO()
                    image_data._pil_image.save(buffer, format="PNG", quality=100)
                    return buffer.getvalue()
                else:
                    # Try to get raw bytes
                    return bytes(image_data)
            else:
                raise GeminiClientError("No images generated by Imagen")
                    
        except Exception as e:
            logger.error(f"Imagen generation failed: {e}")
            raise
    
    def _generate_with_native(
        self, 
        prompt: str, 
        reference_image_bytes: Optional[bytes] = None,
        retry_count: int = 0
    ) -> bytes:
        """
        Generate image using Gemini's native multimodal generation.
        
        Uses the native image generation model from settings.
        """
        # Try native generation model(s) - configurable via settings
        image_models = [
            settings.NATIVE_IMAGE_MODEL_ID,
            settings.IMAGE_MODEL_ID,  # Fallback to main image model
        ]
        
        last_error = None
        
        for model_id in image_models:
            try:
                logger.info(f"Trying native generation with: {model_id}")
                
                contents = [prompt]
                
                # Add reference image if provided
                if reference_image_bytes:
                    mime_type = get_mime_type(reference_image_bytes)
                    image_part = types.Part.from_bytes(
                        data=reference_image_bytes,
                        mime_type=mime_type
                    )
                    contents.append(image_part)
                    contents.append("Use the above garment as reference. Generate a model wearing this exact garment.")

                response = self._client.models.generate_content(
                    model=model_id,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=["image", "text"],
                        temperature=settings.GENERATION_TEMPERATURE,
                    )
                )
                
                # Extract image from response
                if response.candidates:
                    for candidate in response.candidates:
                        if candidate.content and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'inline_data') and part.inline_data:
                                    if part.inline_data.mime_type and part.inline_data.mime_type.startswith('image/'):
                                        logger.info(f"✅ Image generated successfully with {model_id}")
                                        return part.inline_data.data
                
                logger.warning(f"No image in response from {model_id}")
                
            except Exception as e:
                logger.warning(f"Model {model_id} failed: {e}")
                last_error = e
                continue
        
        if last_error:
            raise GeminiClientError(f"Native image generation failed: {last_error}")
        else:
            raise GeminiClientError("No image in response from any model")
    
    def generate_multiple_images(
        self,
        prompt: str,
        count: int = 4,
        reference_image_bytes: Optional[bytes] = None
    ) -> List[bytes]:
        """
        Generate multiple images for selection.
        
        Generating multiple options improves chances of getting a good result.
        
        Args:
            prompt: Image generation prompt
            count: Number of images to generate (1-4)
            reference_image_bytes: Optional reference image
            
        Returns:
            List of generated image bytes
        """
        logger.info(f"Generating {count} images for selection...")
        
        enhanced_prompt = self._enhance_prompt_for_quality(prompt)
        images = []
        
        try:
            if "imagen" in settings.IMAGE_MODEL_ID.lower():
                response = self._client.models.generate_images(
                    model=settings.IMAGE_MODEL_ID,
                    prompt=enhanced_prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=min(count, 4),
                        aspect_ratio=settings.IMAGE_ASPECT_RATIO,
                        safety_filter_level=settings.SAFETY_FILTER_LEVEL,
                    )
                )
                
                if response.generated_images:
                    for img in response.generated_images:
                        if hasattr(img.image, 'image_bytes'):
                            images.append(img.image.image_bytes)
                        elif hasattr(img.image, '_pil_image'):
                            buffer = io.BytesIO()
                            img.image._pil_image.save(buffer, format="PNG", quality=100)
                            images.append(buffer.getvalue())
                            
            logger.info(f"Generated {len(images)} images")
            
        except Exception as e:
            logger.error(f"Multiple image generation failed: {e}")
            # Fall back to single image
            try:
                img = self.generate_image(prompt, reference_image_bytes)
                images.append(img)
            except:
                pass
        
        return images
    
    def compare_images(
        self,
        original_image_bytes: bytes,
        generated_image_bytes: bytes,
        comparison_prompt: str
    ) -> str:
        """
        Compare two images using the text+vision model.
        
        Used by the Quality Checker Agent to verify generated images
        match the original garment.
        """
        logger.info("Comparing original and generated images...")
        
        try:
            original_mime = get_mime_type(original_image_bytes)
            generated_mime = get_mime_type(generated_image_bytes)
            
            original_part = types.Part.from_bytes(data=original_image_bytes, mime_type=original_mime)
            generated_part = types.Part.from_bytes(data=generated_image_bytes, mime_type=generated_mime)
            
            response = self._client.models.generate_content(
                model=settings.TEXT_VISION_MODEL_ID,
                contents=[
                    comparison_prompt,
                    "Original garment image:",
                    original_part,
                    "Generated try-on image:",
                    generated_part,
                ],
                config=types.GenerateContentConfig(
                    temperature=settings.ANALYSIS_TEMPERATURE,
                    max_output_tokens=2048,
                )
            )
            
            if response.text:
                logger.info("Image comparison completed")
                return response.text
            else:
                raise GeminiClientError("Empty comparison response")
                
        except Exception as e:
            logger.error(f"Image comparison failed: {e}")
            raise GeminiClientError(f"Image comparison failed: {e}")


# Singleton instance for easy import
_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """
    Get or create the singleton Gemini client.
    
    Returns:
        Configured GeminiClient instance
    """
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client


def reset_client():
    """Reset the singleton client (useful after config changes)."""
    global _client
    _client = None
    logger.info("Gemini client reset - will reinitialize on next use")
