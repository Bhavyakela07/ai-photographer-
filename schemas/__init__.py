"""Schemas package for AI Virtual Photographer."""
from schemas.garment_schema import (
    GarmentDescription,
    Silhouette,
    Fabric,
    Embroidery,
    Pattern,
    Draping,
    Colors,
)
from schemas.generation_request import (
    Gender,
    PoseStyle,
    BackgroundStyle,
    ModelPreferences,
    GenerationRequest,
    AnalysisResponse,
    GenerationResponse,
    QualityReport,
)

__all__ = [
    # Garment schema
    "GarmentDescription",
    "Silhouette",
    "Fabric",
    "Embroidery",
    "Pattern",
    "Draping",
    "Colors",
    # Request/Response
    "Gender",
    "PoseStyle",
    "BackgroundStyle",
    "ModelPreferences",
    "GenerationRequest",
    "AnalysisResponse",
    "GenerationResponse",
    "QualityReport",
]
