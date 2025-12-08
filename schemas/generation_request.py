"""
Request and response schemas for AI Virtual Photographer API.

These models define the data structures for web UI interactions.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

from schemas.garment_schema import GarmentDescription


class Gender(str, Enum):
    """Target gender for the model in generated image."""
    MALE = "male"
    FEMALE = "female"
    UNISEX = "unisex"


class PoseStyle(str, Enum):
    """Pose style for the generated model."""
    # Standing poses
    STANDING_FRONT = "standing front pose, looking at camera"
    STANDING_SIDE = "standing side pose with slight turn, elegant profile"
    STANDING_THREE_QUARTER = "three-quarter standing pose, body angled 45 degrees"
    STANDING_BACK = "standing back pose showing garment from behind"
    
    # Dynamic poses
    WALKING = "elegant walking pose, mid-stride"
    WALKING_TOWARDS = "walking towards camera with confidence"
    TURNING = "graceful turning pose, fabric flowing"
    
    # Seated poses
    SITTING = "graceful sitting pose on elegant chair"
    SITTING_FLOOR = "sitting on floor in traditional style"
    
    # Traditional Indian poses
    TRADITIONAL_NAMASTE = "traditional Indian pose with hands folded in namaste"
    TRADITIONAL_DANCE = "classical Indian dance pose, expressive mudra"
    TRADITIONAL_BRIDAL = "bridal pose, shy and elegant with dupatta"
    
    # Fashion poses
    FASHION_EDITORIAL = "high fashion editorial pose, dramatic and artistic"
    FASHION_CASUAL = "casual relaxed pose, natural and approachable"
    HAND_ON_HIP = "confident pose with hand on hip"


class BackgroundStyle(str, Enum):
    """Background style for the generated image."""
    # Studio backgrounds
    STUDIO_WHITE = "clean white studio background with soft lighting"
    STUDIO_GRAY = "neutral gray studio background, professional"
    STUDIO_BLACK = "dramatic black studio background with spotlight"
    STUDIO_GRADIENT = "soft gradient studio background, modern look"
    STUDIO_CREAM = "warm cream/beige studio background"
    
    # Indoor settings
    INDOOR_ELEGANT = "elegant indoor setting with subtle luxury decor"
    INDOOR_MODERN = "modern minimalist interior with clean lines"
    INDOOR_TRADITIONAL = "traditional Indian home interior with ethnic decor"
    INDOOR_BOUTIQUE = "fashion boutique setting with mirrors"
    
    # Outdoor settings
    OUTDOOR_GARDEN = "beautiful outdoor garden with flowers and greenery"
    OUTDOOR_SUNSET = "golden hour outdoor setting with warm sunset light"
    OUTDOOR_URBAN = "modern urban setting with city architecture"
    
    # Cultural/Heritage settings
    PALACE = "royal palace or haveli backdrop with ornate architecture"
    TEMPLE = "ancient temple courtyard with traditional architecture"
    HERITAGE = "heritage monument backdrop, cultural setting"
    
    # Special occasions
    WEDDING_MANDAP = "wedding mandap setting with floral decorations"
    FESTIVE = "festive background with lights and decorations"


class ModelPreferences(BaseModel):
    """
    User preferences for the generated model image.
    
    Attributes:
        gender: Target gender of the model (defaults to auto-detect from garment)
        pose: Desired pose style
        background: Background setting
        age_range: Approximate age range description (e.g., "young adult", "middle-aged")
        additional_styling: Any additional styling notes
    """
    gender: Optional[Gender] = Field(None, description="Model gender, auto-detected if not specified")
    pose: PoseStyle = Field(PoseStyle.STANDING_FRONT, description="Pose style")
    background: BackgroundStyle = Field(BackgroundStyle.STUDIO_WHITE, description="Background style")
    age_range: Optional[str] = Field("young adult", description="Age range description")
    additional_styling: Optional[str] = Field(None, description="Additional styling notes")


class GenerationRequest(BaseModel):
    """
    Request to generate a try-on image.
    
    This is what the web UI sends to the generation pipeline.
    """
    # Image is handled separately via file upload
    preferences: ModelPreferences = Field(
        default_factory=ModelPreferences,
        description="Model and image preferences"
    )
    skip_analysis: bool = Field(
        False, 
        description="Skip garment analysis if using cached result"
    )
    cached_description: Optional[GarmentDescription] = Field(
        None,
        description="Previously analyzed garment description"
    )


class AnalysisResponse(BaseModel):
    """
    Response from garment analysis.
    """
    success: bool
    garment_description: Optional[GarmentDescription] = None
    summary: Optional[str] = None
    error: Optional[str] = None


class GenerationResponse(BaseModel):
    """
    Response from try-on image generation.
    """
    success: bool
    generated_image_base64: Optional[str] = None
    prompt_used: Optional[str] = None
    garment_description: Optional[GarmentDescription] = None
    error: Optional[str] = None


class QualityReport(BaseModel):
    """
    Quality check report comparing original and generated images.
    """
    color_match: bool = Field(description="Primary colors match")
    embroidery_match: bool = Field(description="Embroidery style preserved")
    pattern_match: bool = Field(description="Patterns preserved")
    silhouette_match: bool = Field(description="Garment shape preserved")
    overall_score: float = Field(description="Overall quality score 0-1")
    issues: List[str] = Field(default_factory=list, description="List of detected issues")
    recommendations: List[str] = Field(default_factory=list, description="Improvement suggestions")
