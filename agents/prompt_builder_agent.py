"""
Prompt Builder Agent for AI Virtual Photographer.

This agent converts the structured GarmentDescription into a rich,
natural-language prompt optimized for image generation.

The prompt is designed to:
1. Preserve garment details (colors, patterns, embroidery)
2. Describe the model (gender, pose, styling)
3. Set the scene (background, lighting)
4. Emphasize accuracy and realism
"""

from typing import Optional

from schemas.garment_schema import GarmentDescription
from schemas.generation_request import ModelPreferences, Gender, PoseStyle, BackgroundStyle
from utils.logging_utils import get_agent_logger

logger = get_agent_logger("PromptBuilder")


def build_image_prompt(
    garment: GarmentDescription,
    preferences: Optional[ModelPreferences] = None
) -> str:
    """
    Build a detailed image generation prompt from garment description.
    
    This is the main function of the Prompt Builder Agent. It takes
    the structured garment data and user preferences to create
    an optimized prompt for image generation.
    
    Args:
        garment: Structured garment description from Understanding Agent
        preferences: User's preferences for the generated image
    
    Returns:
        A detailed natural-language prompt for image generation
    
    Example:
        >>> prompt = build_image_prompt(garment, ModelPreferences(gender=Gender.MALE))
        >>> print(prompt)
        "Generate a full-body studio photograph of a male Indian model..."
    """
    logger.info("Building image generation prompt...")
    
    # Use defaults if no preferences provided
    if preferences is None:
        preferences = ModelPreferences()
    
    # Determine gender from garment if not specified
    gender = _determine_gender(garment, preferences.gender)
    
    # Build prompt sections
    sections = [
        _build_intro_section(gender, preferences),
        _build_garment_section(garment),
        _build_color_section(garment),
        _build_embroidery_section(garment),
        _build_pattern_section(garment),
        _build_silhouette_section(garment),
        _build_fabric_section(garment),
        _build_styling_section(garment, preferences),
        _build_technical_section(preferences),
        _build_constraints_section(),
    ]
    
    # Combine non-empty sections
    prompt = "\n\n".join(section for section in sections if section)
    
    logger.info(f"Generated prompt ({len(prompt)} chars)")
    logger.debug(f"Full prompt: {prompt}")
    
    return prompt


def _determine_gender(
    garment: GarmentDescription,
    specified_gender: Optional[Gender]
) -> str:
    """Determine the gender for the model based on garment or preference."""
    if specified_gender:
        return specified_gender.value
    
    if garment.gender_usage:
        if "male" in garment.gender_usage:
            return "male"
        elif "female" in garment.gender_usage:
            return "female"
    
    # Default based on garment type
    if garment.garment_type:
        female_garments = ["lehenga", "anarkali", "saree", "salwar", "kurti", "gown"]
        male_garments = ["sherwani", "kurta pajama", "achkan", "jodhpuri"]
        
        garment_lower = garment.garment_type.lower()
        if any(g in garment_lower for g in female_garments):
            return "female"
        if any(g in garment_lower for g in male_garments):
            return "male"
    
    return "female"  # Default


def _build_intro_section(gender: str, preferences: ModelPreferences) -> str:
    """Build the introduction/scene-setting section."""
    age_desc = preferences.age_range or "young adult"
    pose = preferences.pose.value if preferences.pose else "standing front pose"
    
    return f"""Generate a high-quality, professional fashion photography image.

Subject: A {age_desc} {gender} Indian model in a {pose}.
The model should have natural, confident expression and elegant posture.
Professional studio lighting with soft shadows for depth."""


def _build_garment_section(garment: GarmentDescription) -> str:
    """Build the main garment description section."""
    if not garment.garment_type:
        return ""
    
    lines = [f"GARMENT: {garment.garment_type.title()}"]
    
    if garment.occasion:
        lines.append(f"Occasion: Suitable for {', '.join(garment.occasion)}")
    
    if garment.region_inspiration:
        lines.append(f"Style inspiration: {', '.join(garment.region_inspiration)}")
    
    if garment.styling_notes:
        lines.append(f"Design aesthetic: {', '.join(garment.styling_notes)}")
    
    if garment.free_text_description:
        lines.append(f"Details: {garment.free_text_description}")
    
    return "\n".join(lines)


def _build_color_section(garment: GarmentDescription) -> str:
    """Build the color description section."""
    if not garment.colors:
        return ""
    
    lines = ["COLORS (MUST be accurate):"]
    
    if garment.colors.primary:
        lines.append(f"• Primary color: {garment.colors.primary}")
    
    if garment.colors.secondary:
        lines.append(f"• Secondary colors: {', '.join(garment.colors.secondary)}")
    
    if garment.colors.pattern_colors:
        lines.append(f"• Pattern/embroidery colors: {', '.join(garment.colors.pattern_colors)}")
    
    return "\n".join(lines) if len(lines) > 1 else ""


def _build_embroidery_section(garment: GarmentDescription) -> str:
    """Build the embroidery description section."""
    if not garment.embroidery:
        return ""
    
    lines = ["EMBROIDERY (preserve exactly):"]
    
    for i, emb in enumerate(garment.embroidery, 1):
        emb_lines = []
        
        if emb.style:
            emb_lines.append(f"Style: {emb.style}")
        
        if emb.motifs:
            emb_lines.append(f"Motifs: {', '.join(emb.motifs)}")
        
        if emb.density:
            emb_lines.append(f"Density: {emb.density}")
        
        if emb.placement:
            emb_lines.append(f"Placement: {', '.join(emb.placement)}")
        
        if emb_lines:
            prefix = f"• Embroidery {i}: " if len(garment.embroidery) > 1 else "• "
            lines.append(prefix + " | ".join(emb_lines))
    
    return "\n".join(lines) if len(lines) > 1 else ""


def _build_pattern_section(garment: GarmentDescription) -> str:
    """Build the pattern description section."""
    if not garment.patterns:
        return ""
    
    lines = ["PATTERNS (preserve exactly):"]
    
    for i, pattern in enumerate(garment.patterns, 1):
        pattern_lines = []
        
        if pattern.name:
            pattern_lines.append(f"Type: {pattern.name}")
        
        if pattern.shapes:
            pattern_lines.append(f"Shapes: {', '.join(pattern.shapes)}")
        
        if pattern.layout:
            pattern_lines.append(f"Layout: {pattern.layout}")
        
        if pattern.scale:
            pattern_lines.append(f"Scale: {pattern.scale}")
        
        if pattern_lines:
            prefix = f"• Pattern {i}: " if len(garment.patterns) > 1 else "• "
            lines.append(prefix + " | ".join(pattern_lines))
    
    return "\n".join(lines) if len(lines) > 1 else ""


def _build_silhouette_section(garment: GarmentDescription) -> str:
    """Build the silhouette/shape description section."""
    if not garment.silhouette:
        return ""
    
    sil = garment.silhouette
    parts = []
    
    if sil.length:
        parts.append(f"{sil.length} length")
    if sil.fit:
        parts.append(f"{sil.fit} fit")
    if sil.sleeve:
        parts.append(f"{sil.sleeve} sleeves")
    if sil.neckline:
        parts.append(f"{sil.neckline} neckline")
    
    if parts:
        return f"SILHOUETTE: {', '.join(parts)}"
    return ""


def _build_fabric_section(garment: GarmentDescription) -> str:
    """Build the fabric description section."""
    if not garment.fabrics:
        return ""
    
    fabric_descs = []
    for fab in garment.fabrics:
        parts = []
        if fab.name:
            parts.append(fab.name)
        if fab.sheen:
            parts.append(f"{fab.sheen} sheen")
        if fab.approx_weight:
            parts.append(f"{fab.approx_weight} weight")
        if parts:
            fabric_descs.append(", ".join(parts))
    
    if fabric_descs:
        return f"FABRIC: {'; '.join(fabric_descs)}. Show realistic fabric texture and drape."
    return ""


def _build_styling_section(
    garment: GarmentDescription,
    preferences: ModelPreferences
) -> str:
    """Build additional styling notes section."""
    lines = []
    
    if garment.draping:
        draping = garment.draping
        if draping.has_dupatta:
            lines.append("Include dupatta/shawl draped elegantly")
        if draping.layering:
            lines.append(f"Layering: {draping.layering}")
    
    if preferences.additional_styling:
        lines.append(f"Additional styling: {preferences.additional_styling}")
    
    if lines:
        return "STYLING:\n" + "\n".join(f"• {line}" for line in lines)
    return ""


def _build_technical_section(preferences: ModelPreferences) -> str:
    """Build the technical/background section."""
    background = preferences.background.value if preferences.background else "clean white studio background"
    
    return f"""TECHNICAL REQUIREMENTS:
• Background: {background}
• Full-body shot showing complete garment
• High resolution, sharp details
• Natural skin tones and lighting
• Professional fashion photography quality"""


def _build_constraints_section() -> str:
    """Build the constraints section to ensure accuracy."""
    return """CRITICAL CONSTRAINTS:
• The garment design MUST closely match the description above
• Do NOT change or simplify embroidery patterns
• Do NOT alter the color palette
• Preserve all decorative elements in their exact positions
• The garment should look like the SAME garment, not a similar one
• Focus on photorealistic rendering of fabric texture and embroidery"""


def build_simple_prompt(garment: GarmentDescription, gender: str = "female") -> str:
    """
    Build a simpler, more concise prompt for cases where detailed prompt fails.
    
    Args:
        garment: Garment description
        gender: Target gender
    
    Returns:
        A shorter prompt focusing on key details
    """
    parts = [
        f"Professional fashion photography of a {gender} Indian model wearing",
    ]
    
    if garment.garment_type:
        parts.append(f"a beautiful {garment.garment_type}")
    else:
        parts.append("traditional Indian ethnic wear")
    
    if garment.colors and garment.colors.primary:
        parts.append(f"in {garment.colors.primary}")
    
    if garment.embroidery and garment.embroidery[0].style:
        parts.append(f"with {garment.embroidery[0].style} embroidery")
    
    parts.append(". Studio lighting, white background, full body shot, high quality.")
    
    return " ".join(parts)
