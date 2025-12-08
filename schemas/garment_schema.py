"""
Garment schema definitions for AI Virtual Photographer.

These Pydantic models define the structured representation of
Indian ethnic garments. The schema is designed to be:
- Flexible: All fields are optional to handle incomplete information
- Comprehensive: Covers all aspects of ethnic wear (embroidery, patterns, draping)
- Extensible: Lists allow multiple values where applicable
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Silhouette(BaseModel):
    """
    Describes the overall shape and construction of the garment.
    
    Attributes:
        length: How long the garment is (e.g., "knee-length", "ankle-length", "floor-length")
        fit: How the garment fits the body (e.g., "straight", "A-line", "flared", "fitted")
        sleeve: Sleeve style (e.g., "full-sleeve", "half-sleeve", "sleeveless", "three-quarter")
        neckline: Neckline design (e.g., "bandhgala", "V-neck", "round", "mandarin", "boat")
    """
    length: Optional[str] = Field(None, description="Garment length")
    fit: Optional[str] = Field(None, description="Fit style")
    sleeve: Optional[str] = Field(None, description="Sleeve type")
    neckline: Optional[str] = Field(None, description="Neckline style")


class Fabric(BaseModel):
    """
    Describes the fabric/material of the garment.
    
    Attributes:
        name: Fabric type (e.g., "silk", "cotton", "chiffon", "georgette", "velvet")
        approx_weight: Fabric weight (e.g., "light", "medium", "heavy")
        sheen: Fabric shine (e.g., "high", "medium", "matte", "satin-finish")
    """
    name: Optional[str] = Field(None, description="Fabric name")
    approx_weight: Optional[str] = Field(None, description="Fabric weight")
    sheen: Optional[str] = Field(None, description="Fabric sheen/shine level")


class Embroidery(BaseModel):
    """
    Describes embroidery and embellishment details.
    
    Indian ethnic wear is known for intricate embroidery work.
    This model captures the various aspects of the embroidery.
    
    Attributes:
        style: Embroidery technique (e.g., "zari", "zardozi", "phulkari", "chikankari", 
               "mirror work", "thread work", "sequin", "beadwork")
        motifs: List of decorative patterns (e.g., ["circular floral", "paisley", "peacock"])
        density: How dense the embroidery is (e.g., "heavy", "medium", "sparse", "scattered")
        placement: Where the embroidery appears (e.g., ["front panel", "cuffs", "collar", 
                   "hem", "neckline", "border", "all-over"])
    """
    style: Optional[str] = Field(None, description="Embroidery style/technique")
    motifs: List[str] = Field(default_factory=list, description="Decorative motif patterns")
    density: Optional[str] = Field(None, description="Embroidery density")
    placement: List[str] = Field(default_factory=list, description="Where embroidery is placed")


class Pattern(BaseModel):
    """
    Describes printed or woven patterns on the fabric.
    
    Distinct from embroidery, these are inherent to the fabric itself.
    
    Attributes:
        name: Pattern category (e.g., "geometric", "floral", "paisley", "abstract", 
              "stripes", "checks", "ikat", "bandhani")
        shapes: Specific shapes in pattern (e.g., ["circle", "diamond", "leaf", "lotus"])
        layout: How pattern is distributed (e.g., "all-over", "border", "central motif", 
                "scattered", "vertical stripes")
        scale: Size of pattern elements (e.g., "small", "medium", "large", "micro")
    """
    name: Optional[str] = Field(None, description="Pattern category name")
    shapes: List[str] = Field(default_factory=list, description="Shapes in the pattern")
    layout: Optional[str] = Field(None, description="Pattern distribution layout")
    scale: Optional[str] = Field(None, description="Pattern element size")


class Draping(BaseModel):
    """
    Describes layering and draping elements.
    
    Many Indian garments involve multiple layers or draping pieces.
    
    Attributes:
        has_dupatta: Whether garment includes a dupatta/shawl
        layering: Description of layers (e.g., "single-layer", "two-piece", 
                  "lehenga + choli + dupatta", "kurta + jacket")
        hem_style: Bottom edge style (e.g., "straight", "rounded", "asymmetric", "high-low")
    """
    has_dupatta: Optional[bool] = Field(None, description="Includes dupatta/shawl")
    layering: Optional[str] = Field(None, description="Layering description")
    hem_style: Optional[str] = Field(None, description="Hem/bottom edge style")


class Colors(BaseModel):
    """
    Describes the color palette of the garment.
    
    Attributes:
        primary: Main/dominant color (e.g., "deep maroon", "royal blue", "emerald green")
        secondary: Additional colors (e.g., ["gold", "silver", "copper"])
        pattern_colors: Colors used in patterns/embroidery (e.g., ["gold thread", "red sequins"])
    """
    primary: Optional[str] = Field(None, description="Primary/dominant color")
    secondary: List[str] = Field(default_factory=list, description="Secondary colors")
    pattern_colors: List[str] = Field(default_factory=list, description="Colors in patterns/embroidery")


class GarmentDescription(BaseModel):
    """
    Complete structured description of an Indian ethnic garment.
    
    This is the main schema that the Garment Understanding Agent outputs.
    All fields are optional to handle cases where certain details aren't
    visible or determinable from the image.
    
    Example:
        {
            "garment_type": "sherwani",
            "gender_usage": ["male"],
            "occasion": ["wedding", "festive"],
            "colors": {
                "primary": "ivory white",
                "secondary": ["gold"],
                "pattern_colors": ["gold thread", "silver sequins"]
            },
            "embroidery": [{
                "style": "zardozi",
                "motifs": ["paisley", "floral"],
                "density": "heavy",
                "placement": ["front panel", "collar", "cuffs"]
            }]
        }
    """
    # Basic identification
    garment_type: Optional[str] = Field(
        None, 
        description="Type of garment (e.g., kurta, sherwani, lehenga, anarkali, saree blouse)"
    )
    gender_usage: List[str] = Field(
        default_factory=list, 
        description="Target gender(s): male, female, unisex"
    )
    
    # Cultural context
    region_inspiration: List[str] = Field(
        default_factory=list, 
        description="Regional style influences (e.g., North India, Punjab, Rajasthan, South India)"
    )
    occasion: List[str] = Field(
        default_factory=list, 
        description="Suitable occasions (e.g., wedding, festive, casual, formal, party)"
    )
    
    # Physical attributes
    silhouette: Optional[Silhouette] = Field(None, description="Shape and construction details")
    fabrics: List[Fabric] = Field(default_factory=list, description="Fabric/material details")
    colors: Optional[Colors] = Field(None, description="Color palette")
    
    # Decorative elements
    embroidery: List[Embroidery] = Field(default_factory=list, description="Embroidery details")
    patterns: List[Pattern] = Field(default_factory=list, description="Pattern details")
    
    # Construction
    draping: Optional[Draping] = Field(None, description="Layering and draping details")
    
    # Additional context
    styling_notes: List[str] = Field(
        default_factory=list, 
        description="Style notes (e.g., indo-western fusion, traditional, minimalist, royal)"
    )
    free_text_description: Optional[str] = Field(
        None, 
        description="Rich free-form description for nuances not captured in structured fields"
    )
    
    def get_summary(self) -> str:
        """
        Generate a human-readable summary of the garment.
        
        Returns:
            A concise string summarizing the key attributes.
        """
        parts = []
        
        if self.garment_type:
            parts.append(self.garment_type.title())
        
        if self.colors and self.colors.primary:
            parts.append(f"in {self.colors.primary}")
        
        if self.fabrics:
            fabric_names = [f.name for f in self.fabrics if f.name]
            if fabric_names:
                parts.append(f"({', '.join(fabric_names)})")
        
        if self.embroidery:
            styles = [e.style for e in self.embroidery if e.style]
            if styles:
                parts.append(f"with {', '.join(styles)} embroidery")
        
        if self.occasion:
            parts.append(f"for {', '.join(self.occasion)}")
        
        return " ".join(parts) if parts else "Unknown garment"
